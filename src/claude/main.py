import dagger
from dagger import dag, function, object_type
from typing import Dict, Optional
from typing import Annotated
import json
# The idea is to have a simple module that can be used to make requests to the Anthropic API
# With time, we can add more functionality to the module, such as caching, error handling, etc.

# TODO:
# Caching https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

MessageParam = Dict[str, str]  # type alias for {"role": str, "content": str}

@object_type
class Claude:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        return config

    @function
    async def request(self, 
                      dir: dagger.Directory, 
                      prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                      file: Annotated[str, "The path to the file containing the prompt to send to the Anthropic API"] | None,
                      api_key: dagger.Secret) -> str:
        """Makes a call to the Anthropic API and returns the response"""
        input = load_input(prompt, file)
        if isinstance(input, ValueError):
            raise ValueError("The file is not a valid list of MessageParam")
        
        return await (
            dag.container()
            .from_("python:3.12.1")
            # Install anthropic SDK
            .with_exec(["pip", "install", "anthropic"])
            # Mount the source directory
            .with_directory("/app", dir)
            # Set the API key as an environment variable
            .with_secret_variable("ANTHROPIC_API_KEY", api_key)
            # Run the script with the provided prompt
            .with_exec(["python", "/app/chat.py", input])
            .stdout()
        )

    @function
    async def chat(self,
                   dir: dagger.Directory,
                   prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                   role: Annotated[str, "The role of the user"] | None,
                   file: Annotated[str, "The path to the file containing the prompt to send to the Anthropic API"] | None,
                   api_key: dagger.Secret,
                   model: Optional[str] = "claude-3-opus-20240229") -> str:
        """Simplified interface for chatting with Claude"""
        return await self.request(dir, prompt, file, api_key, role)
    
def load_input(prompt: str | None, file: str | None, role: Optional[str] = "user") -> str | ValueError:
    if prompt:
        return json.dumps([{"role": role, "content": prompt}])
    elif file:
        with open(file, 'r') as file:
            if validate_json_contents(file.read()):
                return file.read()
            else:
                raise ValueError("The file is not a valid list of MessageParam")
    else:
        raise ValueError("Either prompt or file must be provided")
    
#check if the files is a valid list of MessageParam
def validate_json_contents(file: str) -> bool:
    try:
        return isinstance(json.loads(file), list)
    except:
        return False

config = {
    "version": "1.0.0",
    "default_model": "claude-3-opus-20240229",
    "max_tokens": 1024,
    "temperature": 0.7,
    "deployment_criteria": {
        "max_latency": 2000,  # ms
        "availability": 0.999
    }
}
