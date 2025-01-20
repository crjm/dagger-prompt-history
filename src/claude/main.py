import dagger
from dagger import dag, function, object_type
from typing import Dict, Optional
from typing import Annotated
import json
# The idea is to have a simple module that can be used to make requests to the Anthropic API
# With time, we can add more functionality to the module, such as caching, error handling, etc.

# TODO:
# Prompt Caching https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
# Dependencies caching with mounted volume

MessageParam = Dict[str, str]  # type alias for {"role": str, "content": str}

@object_type
class Claude:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        return config
    
    @function 
    async def base_container(self,
                             dir: dagger.Directory) -> dagger.Container:
        """Base container for the Claude module"""
        deps = dag.cache_volume("pip")
        return await (
            dag.container()
            .from_("python:3.12.1")
            .with_directory("/app", dir)
            .with_mounted_cache("/root/.cache/pip", deps)
            .with_exec(["pip", "install", "anthropic"])
        )
    
    @function
    async def request(self, 
                      dir: dagger.Directory, 
                      prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                      api_key: dagger.Secret) -> dagger.Container:
        """Makes a call to the Anthropic API and returns the response"""
        input = load_input(prompt)
        if isinstance(input, ValueError):
            raise ValueError("The file is not a valid list of MessageParam")
        
        container = await self.base_container(dir)
        container = container.with_secret_variable("ANTHROPIC_API_KEY", api_key)
        container = container.with_exec(["python", "/app/chat.py", input])

        return await (
            container
        )

    
    @function
    async def dump_db_to_file(self,
                              container: dagger.Container) -> dagger.File:
        """Dumps the database to a file"""
        return await (
            container
            .with_workdir("/app/db")
            .with_exec(["python", "main.py", "dump_db_to_file", "dump_db.json"])
            .file("dump_db.json")
        )

    @function
    async def chat(self,
                   dir: dagger.Directory,
                   prompt: Annotated[str, "The prompt to send to the Anthropic API"] | None,
                   role: Annotated[str, "The role of the user"] | None,
                   api_key: dagger.Secret) -> str:
        """Simplified interface for chatting with Claude"""
        container = await self.request(dir, prompt, api_key)
        return await (
            container
            .stdout()
        )
    
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
