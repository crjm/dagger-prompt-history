import dagger
from dagger import dag, function, object_type
from typing import Dict, Optional
from typing import Annotated
import json
# The idea is to have a simple module that can be used to make requests to the Anthropic API
# With time, we can add more functionality to the module, such as caching, error handling, etc.

# TODO:
# Prompt Caching https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
# Add a way to choose the model
# Add a way to choose the temperature
# Add a way to choose the max tokens
# Add a way to pass a config file to avoid a lot of arguments in the CLI

# Dependencies caching with mounted volume - done
# Chat history persistence with TBD approach
    # - Use a mounted volume - can't be used with export - done
    # - Use a mounted directory - done

DB_PATH = "/app/db/data"

@object_type
class Claude:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        return config
    
    @function 
    async def base_container(self,
                             dir: dagger.Directory,
                             history: dagger.Directory) -> dagger.Container:
        """Base container for the Claude module"""

        deps = dag.cache_volume("pip")

        return await (
            dag.container()
            .from_("python:3.12.1")
            .with_directory("/app", dir)
            .with_mounted_cache("/root/.cache/pip", deps)
            .with_mounted_directory(DB_PATH, history)
            .with_exec(["pip", "install", "anthropic", "requests"])
            .with_exec(["python", "/app/db/main.py", "create_db_if_not_exists"])
        )
    
    @function
    async def export_chat_history(self,
                                  container: dagger.Container) -> dagger.Directory:
        """Exports the chat history to a directory in the host machine.
        
        The directory is mounted in the container at {DB_PATH}
        The host directory is passed as a CLI argument.
        https://docs.dagger.io/cookbook/#export-a-directory-or-file-to-the-host
        """
        return container.directory(DB_PATH)
        
    @function
    async def request(self, 
                      dir: dagger.Directory, 
                      history: dagger.Directory,
                      prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                      api_key: dagger.Secret,
                      svc: dagger.Service) -> dagger.Container:
        """Makes a call to the Anthropic API and returns a container with the response"""
        input = load_input(prompt)
        if isinstance(input, ValueError):
            raise ValueError("The file is not a valid list of MessageParam")
        
        container = await self.base_container(dir, history)
        container = container.with_secret_variable("ANTHROPIC_API_KEY", api_key)
        container = container.with_service_binding("svc", svc)
        container = container.with_exec(["python", "/app/chat.py", input])

        return container

    @function
    async def chat(self,
                   dir: dagger.Directory,
                   history: dagger.Directory,
                   prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                   svc: dagger.Service,
                   api_key: dagger.Secret) -> dagger.Directory:
        """Simplified interface for chatting with Claude"""
        container = await self.request(dir, history, prompt, api_key, svc)
        return await self.export_chat_history(container)
    
def load_input(prompt: str | None, role: Optional[str] = "user") -> str | ValueError:
    if prompt:
        return json.dumps([{"role": role, "content": prompt}])
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
