from typing import Optional, Dict, Union, List, Type
import json
import requests

from superagi.llms.base_llm import BaseLlm
from superagi.helper.error_handler import ErrorHandler
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
    llm: Optional[BaseLlm] = None

    def _execute(self,search_term: str):
        api_url = self.get_tool_config("SEARCH_API_URL")
        api_key = self.get_tool_config("SEARCH_API_KEY")
        
        results = self.search(api_url, api_key, search_term)
        if results:
            return results
        else:
            return f"No articles on {search_term}."

    def search(self,
               api_url: str,
               api_key: str,
               search_term: str) -> List[str]:
        """Search for a given term"""
        request_url = f"{api_url}/document?offset=0&limit=5"
        search_query = {
            "search_term": search_term,
        }

        search_results = send_post_request(request_url, api_key, search_query)
        if search_results and search_results["results"]["documents"]:
            article_ids = []
            results = []
            for hit in search_results["results"]["documents"]:
                article_ids.append(hit.get("document_id"))
                results.append(hit.get("clean_text"))

            summary = self.summarise_result(search_term, results)      

            return summary + "\n\nArticle IDs:\n" + "\n".join("- " + article_id for article_id in article_ids)
        else:
            return None

    def summarise_result(self, query, snippets):
        """
        Summarise the result of a SearchAPI search.

        Args:
            query : The query to search for.
            snippets (list): A list of snippets from the search.

        Returns:
            A summary of the search result.
        """
        summarize_prompt ="""Summarize the following text `{snippets}`
            Write a concise or as descriptive as necessary and attempt to
            answer the query: `{query}` as best as possible. Use markdown formatting for
            longer responses."""

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{query}", query)

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)
        
        if 'error' in result and result['message'] is not None:
            ErrorHandler.handle_openai_errors(self.toolkit_config.session, self.agent_id, self.agent_execution_id, result['message'])
        return result["content"]
