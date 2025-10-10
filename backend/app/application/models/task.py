from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    completed: bool = False


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool

    # Allows us to create Pydantic models from ORM objects
    class Config:
        from_attributes = True
