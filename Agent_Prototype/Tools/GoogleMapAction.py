"""Google Maps integration for Langfun agents."""

from typing import Any, Optional, List, Union, Literal, ClassVar
import os
import traceback
import urllib.parse
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg

class GoogleMapAction(action_lib.Action):
    """Google Maps action for routing and map embedding.
    
    This action allows agents to create routes between locations and generate
    map URLs for embedding in applications. It supports routing with optional
    directions and custom labels.
    """
    
    # Allow attribute modifications at runtime
    allow_symbolic_assignment = True
    
    # Define operations
    operation: Literal["get_route_url", "show_embedding_map"] = "get_route_url"
    
    # Define parameters
    locations: List[str] = []
    route_direction: Optional[str] = None
    labels: Optional[List[str]] = None
    api_key: Optional[str] = None
    
    # Class constants
    google_maps_base_url: ClassVar[str] = "https://www.google.com/maps/dir/"
    google_maps_embed_url: ClassVar[str] = "https://www.google.com/maps/embed/v1/directions"
    
    def _on_bound(self):
        """Initialize and validate parameters."""
        super()._on_bound()  # Always call parent first
        
        # Validate parameters
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate parameters are consistent."""
        # Validate locations list
        if not self.locations or len(self.locations) < 2:
            raise ValueError("At least two locations are required for routing")
        
        # Validate route direction if provided
        if self.route_direction and self.route_direction not in ["driving", "walking", "bicycling", "transit"]:
            raise ValueError(
                "Invalid route_direction. Must be one of: 'driving', 'walking', 'bicycling', 'transit'"
            )
        
        # Validate labels if provided
        if self.labels and len(self.labels) != len(self.locations):
            raise ValueError("If labels are provided, they must match the number of locations")
    
    def call(self, session, *, lm=None, **kwargs):
        """Execute the Google Maps operation.
        
        Args:
            session: The current session context
            lm: Language model (required by interface)
            **kwargs: Additional keyword arguments
            
        Returns:
            For get_route_url: A URL string to Google Maps with the specified route
            For show_embedding_map: An HTML iframe snippet with the embedded map
        """
        try:
            session.info(f"Starting {self.operation} with {len(self.locations)} locations")
            
            result = self._execute_operation()
            
            session.info(f"Completed {self.operation}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to execute {self.operation}: {str(e)}"
            session.error(error_msg)
            session.error(traceback.format_exc())
            raise RuntimeError(error_msg) from e
    
    def _execute_operation(self) -> Any:
        """Execute the specific operation."""
        if self.operation == "get_route_url":
            return self._generate_route_url()
        elif self.operation == "show_embedding_map":
            return self._generate_embed_html()
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")
    
    def _generate_route_url(self) -> str:
        """Generate a Google Maps URL for the specified route.
        
        Returns:
            A URL string to Google Maps with the route.
        """
        # Start with base URL
        url_parts = [self.google_maps_base_url]
        
        # Add each location to the URL, properly encoded
        for i, location in enumerate(self.locations):
            # If labels are provided, use them instead of the raw location
            display_text = self.labels[i] if self.labels and i < len(self.labels) else location
            
            # URL encode the location
            encoded_location = urllib.parse.quote_plus(location)
            url_parts.append(encoded_location + "/")
        
        # Combine all parts
        url = "".join(url_parts)
        
        # Add travel mode if specified
        if self.route_direction:
            travel_mode_param = f"?travelmode={self.route_direction.lower()}"
            url += travel_mode_param
        
        return url
    
    def _generate_embed_html(self) -> str:
        """Generate HTML for embedding a Google Maps directions map.
        
        Returns:
            An HTML iframe string that can be embedded in a webpage.
        """
        # Try to get API key from environment if not provided directly
        api_key = self.api_key or os.environ.get('GOOGLE_MAP_API_KEY')
        
        if not api_key:
            # Return a placeholder message instead of raising an error
            return '<div style="border:1px solid red; padding:10px;">Error: Google Maps API key is required for embedding maps. Please provide an API key.</div>'
        
        # Build the embed URL
        embed_url = f"{self.google_maps_embed_url}?key={api_key}"
        
        # Add origin and destination
        embed_url += f"&origin={urllib.parse.quote_plus(self.locations[0])}"
        embed_url += f"&destination={urllib.parse.quote_plus(self.locations[-1])}"
        
        # Add waypoints if there are more than 2 locations
        if len(self.locations) > 2:
            waypoints = "|".join([
                urllib.parse.quote_plus(loc) 
                for loc in self.locations[1:-1]
            ])
            embed_url += f"&waypoints={waypoints}"
        
        # Add travel mode if specified
        if self.route_direction:
            embed_url += f"&mode={self.route_direction.lower()}"
        
        # Create the iframe HTML
        iframe_html = (
            f'<iframe width="600" height="450" style="border:0" loading="lazy" '
            f'allowfullscreen src="{embed_url}"></iframe>'
        )
        
        return iframe_html

    def __str__(self):
        """Return a string representation of the action."""
        locations_str = ", ".join(self.locations[:2])
        if len(self.locations) > 2:
            locations_str += f" (and {len(self.locations) - 2} more)"
        
        return f"GoogleMapAction({self.operation}: {locations_str})"


# Example usage:
if __name__ == "__main__":
    # Create a model
    model = lf.llms.OpenAI(model="gpt-4")
    
    # Create a session
    session = action_lib.Session()
    
    # Create a route URL
    route_action = GoogleMapAction(
        operation="get_route_url",
        locations=["San Francisco, CA", "Palo Alto, CA", "Mountain View, CA"],
        route_direction="driving",
        labels=["Start at SF", "Stop in Palo Alto", "End at Mountain View"]
    )
    route_url = route_action(session=session, lm=model)
    print(f"Route URL: {route_url}")
    
    # Create an embedded map (will use API key from environment if available)
    embed_action = GoogleMapAction(
        operation="show_embedding_map",
        locations=["San Francisco, CA", "Palo Alto, CA", "Mountain View, CA"],
        route_direction="driving"
        # API key will be taken from environment variable GOOGLE_MAP_API_KEY if not specified
    )
    embed_html = embed_action(session=action_lib.Session(), lm=model)
    print(f"Embed HTML: {embed_html[:100]}...")