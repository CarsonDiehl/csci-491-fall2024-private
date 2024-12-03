from flask import Flask, request, render_template, redirect, jsonify
import time
from src.model.todo import Todo, db, Tag
from peewee import fn

app = Flask(__name__, static_url_path='', static_folder='static')

with db:
    db.create_tables([Todo, Tag])

@app.before_request
def _db_connect():
    db.connect()

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()

def add_view_context(view):
    return ("?view=" + view) if view is not None else ""

def get_the_marquee():
    time.sleep(5)
    return "Lazy loading is awesome and so are marquees"

@app.route('/')
def index():
    return redirect("/todos")

@app.post('/todos')
def create_todos():
    view = request.form.get('view', None)
    selected_tags = request.form.getlist('tags')  # Get selected tag IDs as a list
    priority = int(request.form.get('priority', 3))  # Default to 3 if not set
    todo = Todo(text=request.form['todo'], complete=False, priority=priority, tags=[int(tag_id) for tag_id in selected_tags])
    todo.save()
    return redirect("/todos" + (add_view_context(view)))

@app.post('/todos/<id>/toggle')
def toggle_todo(id):
    view = request.form.get('view', None)
    todo = Todo.find(int(id))
    todo.toggle_complete()
    todo.save()
    query = Todo.all(view)
    sort_order= request.args.get('sort', 'order')  # Default if no sort option is selected

    # Modify query to handle sorting
    if sort_order == 'priority_desc':
        todos = query.order_by(Todo.priority.desc(), Todo.order)  # High to Low
    elif sort_order == 'priority_asc':
        todos = query.order_by(Todo.priority.asc(), Todo.order)  # Low to High
    else:
        todos = query.order_by(Todo.order)
    for todo in todos:
        todo.resolved_tags = [Tag.get_by_id(tag_id) for tag_id in todo.tags]
    return render_template("main.html", todos=todos, view=view,editing=None)

@app.get('/todos/<id>/edit')
def edit_todo(id):
    view = request.args.get('view', None)
    todos = Todo.all(view)
    tags = Tag.all()
    return render_template("index.html", todos=todos, editing=int(id), view=view, tags = tags)

@app.post('/todos/<id>')
def update_todo(id):
    view = request.form.get('view', None)
    todo = Todo.find(int(id))
    todo.text = request.form['todo']
    todo.priority = int(request.form['priority'])  # Update the priority
    todo.tags = request.form.getlist('tags')  # Get selected tag IDs as a list
    todo.save()
    return redirect("/todos" + (add_view_context(view)))

@app.get('/todos/reorder')
def show_reorder_ui():
    view = request.args.get('view', None)
    todos = Todo.all(view)
    todos = todos.order_by(Todo.order)
    return render_template("reorder.html", todos=todos)

@app.post('/todos/reorder')
def update_todo_order():
    view = request.args.get('view', None)
    id_list = request.form.getlist('ids')
    tags = Tag.all()
    Todo.reorder(id_list)
    query = Todo.all(view)
    sort_order = request.args.get('sort', 'order')  # Default if no sort option is selected

    # Modify query to handle sorting
    if sort_order == 'priority_desc':
        todos = query.order_by(Todo.priority.desc(), Todo.order)  # High to Low
    elif sort_order == 'priority_asc':
        todos = query.order_by(Todo.priority.asc(), Todo.order)  # Low to High
    else:
        todos = query.order_by(Todo.order)
    for todo in todos:
        todo.resolved_tags = [Tag.get_by_id(tag_id) for tag_id in todo.tags]
    return render_template("main.html", todos=todos, view=view,editing=None, tags=tags)

@app.get('/todos')
def all_todos():
    view = request.args.get('view', None)
    search = request.args.get('q', None)
    tag_filter = request.args.get('tag_filter', None)
    sort_order = request.args.get('sort', 'order')  # Default if no sort option is selected

    query = Todo.all(view,search)
    # Filter by tag if tag_filter is provided
    if tag_filter and tag_filter != 'default':
        # Use a raw SQL query to filter JSON array
        query = query.where(
            fn.json_extract(Todo.tags, '$').contains(tag_filter)
        )

    # Modify query to handle sorting
    if sort_order == 'priority_desc':
        todos = query.order_by(Todo.priority.desc(), Todo.order)  # High to Low
    elif sort_order == 'priority_asc':
        todos = query.order_by(Todo.priority.asc(), Todo.order)  # Low to High
    else:
        todos = query.order_by(Todo.order)
    # Resolve tag names for each TODO
    for todo in todos:
        todo.resolved_tags = [Tag.get_by_id(tag_id) for tag_id in todo.tags]
    if request.headers.get('HX-Request'):
        return render_template("todos_list.html", todos=todos)
    tags=Tag.all()
    return render_template("index.html", todos=todos, view=view, search=search, tags=tags, tag_filter=tag_filter)



@app.post('/voice-input')
def voice_input():
    try:
        data = request.get_json()
        todo_text = data.get('todo', '').strip()
        if not todo_text:
            return jsonify({'error': 'No todo text provided'}), 400
        todo = Todo(text=todo_text, complete=False)
        todo.save()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get("/new_tag")
def new_tag():
    return render_template('new_tag.html')

@app.post("/add_tag")
def add_tag():
    new_tag_name = request.form.get("new_tag")
    tag_color = request.form.get("tag_color", "#0f0f0f")  # Default color if none provided

    if new_tag_name:
        # Add the new tag to the database
        new_tag = Tag(name=new_tag_name, color=tag_color)
        new_tag.save()
    return redirect('/todos')

if __name__ == '__main__':
    app.run(port=5000)