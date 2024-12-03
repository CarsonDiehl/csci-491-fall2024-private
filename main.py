from flask import Flask, request, render_template, redirect, jsonify
import time
from src.model.todo import Todo, db, Tag

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
    priority = int(request.form.get('priority', 3))  # Default to 3 if not set
    todo = Todo(text=request.form['todo'], complete=False, priority=priority)
    todo.save()
    return redirect("/todos" + (add_view_context(view)))

@app.post('/todos/<id>/toggle')
def toggle_todo(id):
    view = request.form.get('view', None)
    todo = Todo.find(int(id))
    todo.toggle_complete()
    todo.save()
    todos = Todo.all(view)
    return render_template("main.html", todos=todos, view=view,editing=None)

@app.get('/todos/<id>/edit')
def edit_todo(id):
    view = request.args.get('view', None)
    todos = Todo.all(view)
    return render_template("index.html", todos=todos, editing=int(id), view=view)

@app.post('/todos/<id>')
def update_todo(id):
    view = request.form.get('view', None)
    todo = Todo.find(int(id))
    todo.text = request.form['todo']
    todo.save()
    return redirect("/todos" + (add_view_context(view)))

@app.post('/todos/<id>/update')
def update_todo_priority(id):
    try:
        view = request.form.get('view', None)
        todo = Todo.find(int(id))
        todo.priority = int(request.form['priority'])  # Update the priority
        todo.save()
        todos = Todo.all(view)
        return render_template("main.html", todos=todos, view=view, editing=None)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.get('/todos/reorder')
def show_reorder_ui():
    view = request.args.get('view', None)
    todos = Todo.all(view)
    return render_template("reorder.html", todos=todos)

@app.post('/todos/reorder')
def update_todo_order():
    view = request.args.get('view', None)
    id_list = request.form.getlist('ids')
    Todo.reorder(id_list)
    todos = Todo.all(view)
    return render_template("main.html", todos=todos, view=view,editing=None)

@app.get('/todos')
def all_todos():
    view = request.args.get('view', None)
    search = request.args.get('q', None)
    sort_order = request.args.get('sort', 'order')  # Default if no sort option is selected
    # Modify query to handle sorting
    if sort_order == 'priority_desc':
        todos = Todo.all(view,search).order_by(Todo.priority.desc(), Todo.order)  # High to Low
    elif sort_order == 'priority_asc':
        todos = Todo.all(view,search).order_by(Todo.priority.asc(), Todo.order)  # Low to High
    else:
        todos = Todo.all(view,search).order_by(Todo.order)
    if request.headers.get('HX-Request'):
        return render_template("todos_list.html", todos=todos)
    tags=Tag.all()
    return render_template("index.html", todos=todos, view=view, search=search, tags=tags)



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