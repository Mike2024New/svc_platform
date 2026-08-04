from pydantic import BaseModel


class SchemaSettings(BaseModel):
    name: str = 'template_svc'
    server_name: str = 'server'
    engine_name: str = 'engine'
