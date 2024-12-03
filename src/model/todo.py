from peewee import *
import logging
from playhouse.sqlite_ext import JSONField

db = SqliteDatabase('todos.db')

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Todo(Model):
    text = CharField()
    complete = BooleanField()
    order = IntegerField(null=True)
    priority = IntegerField(default=3)  # Priority, where 1 is highest and 3 is lowest
    tags = JSONField(default=list)  # Store tag IDs as a list

    def toggle_complete(self):
        self.complete = not self.complete

    @classmethod
    def all(cls, view, search=None):
        select = Todo.select()
        if view == "active":
            select = select.where(Todo.complete == False)
        if view == "complete":
            select = select.where(Todo.complete == True)
        if search:
            select = select.where(Todo.text.ilike("%" + search + "%"))
        return select.order_by(Todo.priority, Todo.order)  # Order by priority first

    @classmethod
    def find(cls, todo_id):
        return Todo.get(Todo.id == todo_id)

    @classmethod
    def reorder(cls, id_list):
        i = 0
        for tid in id_list:
            todo = Todo.find(int(tid))
            todo.order = i
            i = i + 1
            todo.save()

    class Meta:
        database = db

class Tag(Model):
    name = CharField()
    color = CharField()  # Stores color as a string, e.g., "#FF5733"

    @classmethod
    def all(cls):
        select = Tag.select()
        return select

    class Meta:
        database = db

