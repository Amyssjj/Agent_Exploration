# Langfun Apps

This repository contains various applications built with langfun, a framework for language function programming.

## Structure

- `Agents/`: Contains multi-agent notebooks and agent implementations
  - `MultiAgent_TripPlanner.ipynb`: Trip planning agent using multiple specialized agents
  
- `Data/`: Storage for data files used by applications
  - Example itineraries and travel plans

- `Tools/`: Custom actions and utility functions
  - `GoogleMapAction.py`: Integration with Google Maps for route planning and embedding
  - `NotionAction.py`: Allows posting content to Notion
  - `FileSystem.py`, `SearchAction.py`: Utility actions for file operations and search

- `MCPs/`: Model Context Protocol implementations (optional)

## Setup

1. Create a Python environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create .env file with your API keys
cp .env.template .env
# Edit the .env file with your actual API keys
```

## Usage

The primary way to use these tools is through the Jupyter notebooks in the `Agents/` directory.

For example, to run the trip planner:
1. Open `Agents/MultiAgent_TripPlanner.ipynb`
2. Configure your trip preferences in the notebook
3. Run all cells to generate and visualize your itinerary

## Dependencies

- langfun
- pyglove
- openai (or other LLM providers)
- notion-client (for Notion integration)
- pandas, numpy (for data processing)
- IPython (for notebook display)

## License

This project is available for open use and modification.