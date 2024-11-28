from fluid_api_agent.main import (
    fluid_api_request,
)

# Example 1: Basic API Request
basic_request = fluid_api_request(
    "Generate an API request to login to discord https://discord.com/login"
)

print(basic_request.model_dump_json(indent=4))