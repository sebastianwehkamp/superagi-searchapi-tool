from typing import List

from superagi.tools.base_tool import BaseToolkit, BaseTool

from searchapi_tool import SearchAPITool


class MyToolkit(BaseToolkit):
    name: str = "SearchAPI Toolkit"
    description: str = "Editorial Agent toolkit"

    def get_tools(self) -> List[BaseTool]:
        return [SearchAPITool()]

    def get_env_keys(self) -> List[str]:
        return []
