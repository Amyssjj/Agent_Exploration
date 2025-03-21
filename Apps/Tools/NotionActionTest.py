"""Unit tests for the NotionAction class."""

import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import json
from NotionAction import NotionAction, NOTION_AVAILABLE

# Skip all tests if Notion client is not available
@unittest.skipIf(not NOTION_AVAILABLE, "notion-client package is not installed")
class TestNotionAction(unittest.TestCase):
    """Test cases for the NotionAction class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock session
        self.mock_session = MagicMock()
        self.mock_session.info = MagicMock()
        self.mock_session.error = MagicMock()
        
        # Create a mock model
        self.mock_model = MagicMock()
        
        # Create a test token to use
        self.test_token = "test-notion-token"
        os.environ["NOTION_API_TOKEN"] = self.test_token
        
        # Sample data
        self.page_id = "8a4a65ff563e4c70a931800a9e90d94c"
        self.database_id = "3a87fb3b75e741f9864c29dae04a4f9b"
        
        # URL samples
        self.page_url = f"https://www.notion.so/myworkspace/{self.page_id}-Test-Page"
        self.database_url = f"https://www.notion.so/myworkspace/{self.database_id}?v=123456"
        
        # Create patch for the Notion client
        self.client_patcher = patch('NotionAction.Client')
        self.mock_client_cls = self.client_patcher.start()
        self.mock_client = self.mock_client_cls.return_value
        
        # Set up mock methods for the client
        self.mock_client.pages = MagicMock()
        self.mock_client.pages.retrieve = MagicMock()
        self.mock_client.pages.create = MagicMock()
        self.mock_client.pages.update = MagicMock()
        
        self.mock_client.databases = MagicMock()
        self.mock_client.databases.retrieve = MagicMock()
        self.mock_client.databases.query = MagicMock()
        self.mock_client.databases.create = MagicMock()
        self.mock_client.databases.update = MagicMock()
        
        self.mock_client.blocks = MagicMock()
        self.mock_client.blocks.children = MagicMock()
        self.mock_client.blocks.children.list = MagicMock()
        self.mock_client.blocks.children.append = MagicMock()
        self.mock_client.blocks.update = MagicMock()
        
        self.mock_client.search = MagicMock()
        self.mock_client.users = MagicMock()
        self.mock_client.users.list = MagicMock()
    
    def tearDown(self):
        """Clean up after each test."""
        self.client_patcher.stop()
        if "NOTION_API_TOKEN" in os.environ:
            del os.environ["NOTION_API_TOKEN"]
    
    def test_initialization(self):
        """Test basic initialization and parameter validation."""
        # Test valid initialization
        action = NotionAction(operation="read_page", page_id=self.page_id)
        self.assertEqual(action.operation, "read_page")
        self.assertEqual(action.page_id, self.page_id)
        
        # Test client initialization
        self.mock_client_cls.assert_called_once_with(
            auth=self.test_token, 
            api_version=NotionAction.notion_api_version
        )
        
        # Should not raise any validation errors
        action(session=self.mock_session, lm=self.mock_model)
        self.mock_session.error.assert_not_called()
    
    def test_url_extraction(self):
        """Test URL extraction for page and database IDs."""
        # Test page URL extraction
        page_action = NotionAction(operation="read_page", url=self.page_url)
        self.assertEqual(page_action.page_id, self.page_id)
        
        # Test database URL extraction
        db_action = NotionAction(operation="query_database", url=self.database_url)
        self.assertEqual(db_action.database_id, self.database_id)
        
        # Test URL with dash format
        dash_url = f"https://www.notion.so/{self.page_id}-My-Page-Title"
        dash_action = NotionAction(operation="read_page", url=dash_url)
        self.assertEqual(dash_action.page_id, self.page_id)
        
        # Test URL with ID embedded in path
        embedded_url = f"https://www.notion.so/username/Project-Notes-{self.page_id}"
        embedded_action = NotionAction(operation="read_page", url=embedded_url)
        self.assertEqual(embedded_action.page_id, self.page_id)
    
    def test_url_extraction_edge_cases(self):
        """Test edge cases in URL extraction."""
        # Test with invalid URL - should not raise but return error in call
        invalid_action = NotionAction(operation="read_page", url="https://example.com/not-notion")
        result = invalid_action(session=self.mock_session, lm=self.mock_model)
        self.assertTrue("error" in result)
        
        # Test with no ID in URL - should not raise but return error in call
        no_id_action = NotionAction(operation="read_page", url="https://www.notion.so/myworkspace/")
        result = no_id_action(session=self.mock_session, lm=self.mock_model)
        self.assertTrue("error" in result)
        
        # Test with ID provided directly and URL (ID should take precedence)
        action = NotionAction(
            operation="read_page", 
            page_id="direct_page_id", 
            url=self.page_url
        )
        self.assertEqual(action.page_id, "direct_page_id")  # Direct ID should be used
    
    def test_token_handling(self):
        """Test API token handling."""
        # Test with token from environment
        action1 = NotionAction(operation="read_page", page_id=self.page_id)
        action1(session=self.mock_session, lm=self.mock_model)
        
        # Test with direct token
        direct_token = "direct-token-123"
        action2 = NotionAction(operation="read_page", page_id=self.page_id, token=direct_token)
        
        # Direct token should override environment token
        self.mock_client_cls.reset_mock()
        action2(session=self.mock_session, lm=self.mock_model)
        self.mock_client_cls.assert_called_once_with(
            auth=direct_token, 
            api_version=NotionAction.notion_api_version
        )
        
        # Test without any token
        del os.environ["NOTION_API_TOKEN"]
        action3 = NotionAction(operation="read_page", page_id=self.page_id)
        result = action3(session=self.mock_session, lm=self.mock_model)
        self.assertTrue("error" in result)
        self.assertIn("API token not provided", result["error"])
    
    def test_read_page(self):
        """Test read_page operation."""
        # Set up mock responses
        mock_page = {
            "id": self.page_id,
            "properties": {
                "title": {
                    "title": [
                        {"plain_text": "Test Page"}
                    ]
                }
            }
        }
        mock_blocks = {
            "results": [
                {"type": "paragraph", "paragraph": {"text": [{"plain_text": "Test content"}]}}
            ],
            "has_more": False
        }
        
        self.mock_client.pages.retrieve.return_value = mock_page
        self.mock_client.blocks.children.list.return_value = mock_blocks
        
        # Reset any error state
        self.mock_session.error.reset_mock()
        
        # Execute the action
        action = NotionAction(operation="read_page", page_id=self.page_id)
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result["page"], mock_page)
        self.assertEqual(result["blocks"], mock_blocks["results"])
        
        # Verify method calls
        self.mock_client.pages.retrieve.assert_called_once_with(self.page_id)
        self.mock_client.blocks.children.list.assert_called_once_with(
            block_id=self.page_id,
            start_cursor=None
        )
    
    def test_get_page_info(self):
        """Test get_page_info operation."""
        # Set up mock responses
        mock_page = {
            "id": self.page_id,
            "url": "https://www.notion.so/Test-Page-" + self.page_id,
            "created_time": "2023-01-01T12:00:00.000Z",
            "last_edited_time": "2023-01-02T12:00:00.000Z",
            "parent": {"type": "workspace"},
            "properties": {
                "title": {
                    "type": "title",
                    "title": [
                        {"plain_text": "Test Page"}
                    ]
                },
                "Status": {
                    "type": "select",
                    "select": {
                        "name": "In Progress"
                    }
                }
            }
        }
        mock_blocks = {
            "results": [{"id": "block1"}, {"id": "block2"}],
            "has_more": False
        }
        
        self.mock_client.pages.retrieve.return_value = mock_page
        self.mock_client.blocks.children.list.return_value = mock_blocks
        
        # Execute the action
        action = NotionAction(operation="get_page_info", page_id=self.page_id)
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result["id"], self.page_id)
        self.assertEqual(result["title"], "Test Page")
        self.assertEqual(result["block_count"], 2)
        self.assertEqual(result["properties"]["Status"], "In Progress")
        
        # Verify method calls
        self.mock_client.pages.retrieve.assert_called_once_with(self.page_id)
    
    def test_create_page(self):
        """Test create_page operation."""
        # Set up mock responses
        mock_created_page = {
            "id": "new_page_id",
            "url": "https://www.notion.so/New-Page-new_page_id"
        }
        
        self.mock_client.pages.create.return_value = mock_created_page
        
        # Test properties
        test_properties = {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": "New Test Page"
                        }
                    }
                ]
            }
        }
        
        # Execute the action
        action = NotionAction(
            operation="create_page",
            parent_id=self.database_id,
            parent_type="database",
            properties=test_properties
        )
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result, mock_created_page)
        
        # Verify method calls
        self.mock_client.pages.create.assert_called_once_with(
            parent={"database_id": self.database_id},
            properties=test_properties
        )
    
    def test_update_page(self):
        """Test update_page operation."""
        # Set up mock responses
        mock_updated_page = {
            "id": self.page_id,
            "url": "https://www.notion.so/Test-Page-" + self.page_id
        }
        
        mock_blocks = {
            "results": [],
            "has_more": False
        }
        
        self.mock_client.pages.update.return_value = mock_updated_page
        self.mock_client.blocks.children.list.return_value = mock_blocks
        
        # Test properties
        test_properties = {
            "Status": {
                "select": {
                    "name": "Done"
                }
            }
        }
        
        # Execute the action
        action = NotionAction(
            operation="update_page",
            page_id=self.page_id,
            properties=test_properties
        )
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result, mock_updated_page)
        
        # Verify method calls
        self.mock_client.pages.update.assert_called_once_with(
            page_id=self.page_id,
            properties=test_properties
        )
    
    def test_query_database(self):
        """Test query_database operation."""
        # Set up mock responses
        mock_results = {
            "results": [
                {"id": "page1", "properties": {}},
                {"id": "page2", "properties": {}}
            ],
            "has_more": False
        }
        
        self.mock_client.databases.query.return_value = mock_results
        
        # Test filter
        test_filter = {
            "property": "Status",
            "select": {
                "equals": "Done"
            }
        }
        
        # Execute the action
        action = NotionAction(
            operation="query_database",
            database_id=self.database_id,
            query_filter=test_filter,
            limit=10
        )
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result, mock_results)
        
        # Verify method calls
        self.mock_client.databases.query.assert_called_once_with(
            database_id=self.database_id,
            filter=test_filter,
            page_size=10
        )
    
    def test_get_database_info(self):
        """Test get_database_info operation."""
        # Set up mock responses
        mock_database = {
            "id": self.database_id,
            "url": "https://www.notion.so/Test-Database-" + self.database_id,
            "title": [{"plain_text": "Test Database"}],
            "created_time": "2023-01-01T12:00:00.000Z",
            "last_edited_time": "2023-01-02T12:00:00.000Z",
            "properties": {
                "Name": {
                    "type": "title"
                },
                "Status": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "To Do"},
                            {"name": "In Progress"},
                            {"name": "Done"}
                        ]
                    }
                }
            }
        }
        
        mock_rows = {
            "results": [{"id": "row1"}, {"id": "row2"}],
            "has_more": True
        }
        
        self.mock_client.databases.retrieve.return_value = mock_database
        self.mock_client.databases.query.return_value = mock_rows
        
        # Execute the action
        action = NotionAction(operation="get_database_info", database_id=self.database_id)
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result["id"], self.database_id)
        self.assertEqual(result["title"], "Test Database")
        self.assertEqual(result["sample_rows_count"], 2)
        self.assertTrue("Status" in result["property_schema"])
        self.assertEqual(result["property_schema"]["Status"]["type"], "select")
        
        # Verify method calls
        self.mock_client.databases.retrieve.assert_called_once_with(self.database_id)
    
    def test_search(self):
        """Test search operation."""
        # Set up mock responses
        mock_search_results = {
            "results": [
                {"object": "page", "id": "page1"},
                {"object": "database", "id": "db1"}
            ],
            "has_more": False
        }
        
        self.mock_client.search.return_value = mock_search_results
        
        # Execute the action
        action = NotionAction(
            operation="search",
            search_query="test",
            limit=10
        )
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result, mock_search_results)
        
        # Verify method calls
        self.mock_client.search.assert_called_once_with(
            query="test",
            page_size=10
        )
    
    def test_list_users(self):
        """Test list_users operation."""
        # Set up mock responses
        mock_users = {
            "results": [
                {"id": "user1", "name": "User One"},
                {"id": "user2", "name": "User Two"}
            ]
        }
        
        self.mock_client.users.list.return_value = mock_users
        
        # Execute the action
        action = NotionAction(operation="list_users")
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(result, mock_users)
        
        # Verify method calls
        self.mock_client.users.list.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling for various error conditions."""
        # Test API error
        self.mock_client.pages.retrieve.side_effect = Exception("API Error")
        
        action = NotionAction(operation="read_page", page_id=self.page_id)
        result = action(session=self.mock_session, lm=self.mock_model)
        
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "API Error")
        self.assertEqual(result["operation"], "read_page")
        self.assertTrue("traceback" in result)
        
        # Verify session logging
        self.mock_session.error.assert_called()
    
    def test_pagination(self):
        """Test pagination handling for operations that may return multiple pages of results."""
        # Set up mock responses for paginated blocks
        mock_page = {"id": self.page_id, "properties": {}}
        
        # First page of blocks
        first_page = {
            "results": [{"id": "block1"}, {"id": "block2"}],
            "has_more": True,
            "next_cursor": "cursor1"
        }
        
        # Second page of blocks (last page)
        second_page = {
            "results": [{"id": "block3"}],
            "has_more": False
        }
        
        self.mock_client.pages.retrieve.return_value = mock_page
        self.mock_client.blocks.children.list.side_effect = [first_page, second_page]
        
        # Execute the action
        action = NotionAction(operation="read_page", page_id=self.page_id)
        result = action(session=self.mock_session, lm=self.mock_model)
        
        # Verify results
        self.assertEqual(len(result["blocks"]), 3)  # Should have combined both pages
        self.assertEqual(result["blocks"][0]["id"], "block1")
        self.assertEqual(result["blocks"][2]["id"], "block3")
        
        # Verify method calls - should have been called twice with different cursor
        self.mock_client.blocks.children.list.assert_any_call(
            block_id=self.page_id,
            start_cursor=None
        )
        self.mock_client.blocks.children.list.assert_any_call(
            block_id=self.page_id,
            start_cursor="cursor1"
        )

    def test_property_simplification(self):
        """Test the property simplification helper method."""
        # Create a sample of complex properties
        complex_properties = {
            "Title": {
                "type": "title",
                "title": [{"plain_text": "Sample Title"}]
            },
            "Description": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "Sample description text"}]
            },
            "Status": {
                "type": "select",
                "select": {"name": "In Progress"}
            },
            "Tags": {
                "type": "multi_select",
                "multi_select": [{"name": "Tag1"}, {"name": "Tag2"}]
            },
            "Done": {
                "type": "checkbox",
                "checkbox": False
            },
            "Due Date": {
                "type": "date",
                "date": {"start": "2023-05-01", "end": None}
            }
        }
        
        # Create an action instance to test internal method
        action = NotionAction(operation="read_page", page_id=self.page_id)
        simplified = action._simplify_properties(complex_properties)
        
        # Verify simplification
        self.assertEqual(simplified["Title"], "Sample Title")
        self.assertEqual(simplified["Description"], "Sample description text")
        self.assertEqual(simplified["Status"], "In Progress")
        self.assertEqual(simplified["Tags"], ["Tag1", "Tag2"])
        self.assertEqual(simplified["Done"], False)
        self.assertEqual(simplified["Due Date"], "2023-05-01")

    def test_database_schema_simplification(self):
        """Test the database schema simplification."""
        # Create a sample database schema
        schema = {
            "Name": {
                "type": "title"
            },
            "Status": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "To Do"},
                        {"name": "In Progress"},
                        {"name": "Done"}
                    ]
                }
            },
            "Priority": {
                "type": "multi_select",
                "multi_select": {
                    "options": [
                        {"name": "High"},
                        {"name": "Medium"},
                        {"name": "Low"}
                    ]
                }
            }
        }
        
        # Create an action instance to test internal method
        action = NotionAction(operation="get_database_info", database_id=self.database_id)
        simplified = action._simplify_database_schema(schema)
        
        # Verify simplification
        self.assertEqual(simplified["Name"]["type"], "title")
        self.assertEqual(simplified["Status"]["type"], "select")
        self.assertEqual(simplified["Status"]["options"], ["To Do", "In Progress", "Done"])
        self.assertEqual(simplified["Priority"]["type"], "multi_select")
        self.assertEqual(simplified["Priority"]["options"], ["High", "Medium", "Low"])

if __name__ == "__main__":
    unittest.main()