from typing import Optional, Dict, Union, List, Type
import json
import requests

from superagi.tools.base_tool import BaseTool
from pydantic import BaseModel, Field


def send_post_request(api_url: str,
                      api_key: str,
                      data: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int]]]:
    """
    Send a POST request to an API with the specified headers and JSON body.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key to include in the headers.
        data (dict): The data to send in the request body as a JSON payload.

    Returns:
        dict: The JSON response data if the request is successful, or None if it fails.
    """
    # Define headers
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Convert the data to JSON
    json_data = json.dumps(data)

    # Make the POST request
    response = requests.post(api_url, data=json_data, headers=headers)

    # Check the response
    if response.status_code == 200:
        # Request was successful
        response_data = response.json()
        return response_data
    else:
        print(f"Request failed with status code {response.status_code}:")
        print(response.text)
        return None


def search(api_url: str, api_key: str, search_term: str) -> List[str]:
    """Search for a given term"""
    request_url = f"{api_url}/document?offset=0&limit=3"
    search_query = {
        "search_term": search_term,
    }

    search_results = send_post_request(request_url, api_key, search_query)
    if search_results and search_results["results"]["documents"]:
        top_hits = {}
        for hit in search_results["results"]["documents"]:
            top_hits[hit.get("document_id")] = hit.get("clean_text")

        return json.dumps(top_hits)
    else:
        return None


class SearchAPIInput(BaseModel):
    """Inputs for search function"""
    search_term: str = Field(..., description="Term to find news for.")


class SearchAPITool(BaseTool):
    name: str = "Search API Connector"
    description = """
        Use this tool when you need to retrieve the latest article IDs and text for a given search term from the Search API.
        Given a search term and issues title, this tool will return the top 5 news article ids and texts.
        To use the tool, you must provide at least the following parameters:
        ['search_term']

        Summarize every article to 1 sentence and create an appropriate title. Show the article ID for every article.
        """
    args_schema: Type[BaseModel] = SearchAPIInput

    def _execute(self,search_term: str):
        api_url = self.get_tool_config("SEARCH_API_URL")
        api_key = self.get_tool_config("SEARCH_API_KEY")
        
        results = search(api_url, api_key, search_term)
        if results:
            return results
        else:
            return f"No articles on {search_term}."
