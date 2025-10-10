# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database.setup import get_db
# from presentation.routes.healthcheck import router
# from application.task_service import TaskService
# from application.models.task import TaskCreate, TaskResponse
# from application.models.healthcheck import HealthcheckResponse
# from typing import List
# from persistence.task_repository import TaskRepository


# @router.post("/tasks", response_model=TaskResponse)
# def create_task(task: TaskCreate, db: Session = Depends(get_db)):
#     task_repository = TaskRepository(db)
#     service = TaskService(task_repository)
#     return service.create_task(task)


# @router.get("/tasks", response_model=List[TaskResponse])
# def get_tasks(db: Session = Depends(get_db)):
#     task_repository = TaskRepository(db)
#     service = TaskService(task_repository)
#     return service.get_all_tasks()
