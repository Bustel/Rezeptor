import sqlite3
import datetime
from flask import Flask, request, abort, jsonify, render_template, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

DB_PATH = '/home/sebastian/PycharmProjects/Rezeptor/recipe_db'


# TODO Sanitize Database Inputs against XSS Attacks

def dict_from_row(row):
    d = {}
    for key in row.keys():
        d[key] = row[key]
    return d


def get_recipe(recipe_id):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('''SELECT * FROM recipes WHERE id=?''', [recipe_id])
        r = cur.fetchone()

        if r is None:
            abort(404)
            return
        
        recipe_dict = dict_from_row(r)

        cur.execute('''SELECT ingredient, ingredients.name, quantity, unit FROM recipe_ingredients
                             INNER JOIN ingredients ON ingredient = ingredients.id WHERE recipe = ?
                           ''', [recipe_id])
        recipe_dict['ingredients'] = [dict_from_row(row) for row in cur.fetchall()]

        cur.execute('''SELECT path FROM pictures WHERE id=?''', [recipe_dict['pic_id']])
        r = cur.fetchone()
        if r:
            recipe_dict['image'] = r['path']

        cur.execute('''SELECT nr, description FROM recipe_steps WHERE recipe=?''', [recipe_id])
        recipe_dict['steps'] = [dict_from_row(row) for row in cur.fetchall()]

    return recipe_dict


@app.route('/', methods=['GET'])
def index_view():
    return render_template('index2.html')


@app.route('/recipe', methods=['GET'])
def recipe_new():
    return render_template('recipeCtrl.html', recipe_id='null')


@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):
    return render_template('recipeCtrl.html', recipe_id=recipe_id)


@app.route('/uploads/<path:filename>')
def serve_upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/api/recipe', methods=['GET', 'POST', 'PUT', 'DELETE'])
def recipe_endpoint():
    if request.method == 'GET':
        try:
            recipe_id = int(request.args.get('id'))
        except ValueError:
            abort(400)
            return

        recipe_dict = get_recipe(recipe_id)
        return jsonify(recipe_dict)

    elif request.method == 'POST':
        params = request.get_json()

        if params is None:
            abort(400)
            return

        # A new recipe should have at least a name
        name = params['name']

        if name is None:
            abort(400)
            return

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            now = datetime.datetime.now()
            cur.execute('''INSERT INTO recipes (name, created) VALUES (?,?)''', [name, now])
            recipe_id = cur.lastrowid

            if 'ingredients' in params:
                print(params)
                generator = ((None, recipe_id, i['ingredient'], i['quantity'], i['unit']) for i in params['ingredients'])
                cur.executemany('''INSERT INTO recipe_ingredients VALUES (?, ? , ?, ?, ?)''', generator)

            if 'steps' in params:
                generator = ((s['nr'], recipe_id, s['description']) for s in params['steps'])
                cur.executemany('''INSERT INTO recipe_steps VALUES (?,?,?)''', generator)

        # Return newly created recipe
        return jsonify(get_recipe(recipe_id))

    elif request.method == 'PUT':
        params = request.get_json()

        if params is None:
            abort(400)
            return

        # Throws key error and responds 403 if something is missing
        recipe_id = params['id']

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute('''PRAGMA FOREIGN_KEYS=ON''')
            if 'name' in params:
                cur.execute('''UPDATE recipes SET name = ? WHERE id = ?''', [params['name'], recipe_id])

            if 'ingredients' in params:
                cur.execute('''DELETE FROM recipe_ingredients WHERE recipe = ?''', [recipe_id])
                generator = ((None, recipe_id, i['ingredient'], i['quantity'], i['unit']) for i in
                             params['ingredients'])
                cur.executemany('''INSERT INTO recipe_ingredients VALUES (?, ? , ?, ?, ?)''', generator)

            if 'steps' in params:
                cur.execute('''DELETE FROM recipe_steps WHERE recipe = ?''', [recipe_id])
                generator = ((s['nr'], recipe_id, s['description']) for s in params['steps'])
                cur.executemany('''INSERT INTO recipe_steps VALUES (?,?,?)''', generator)

        return jsonify(get_recipe(recipe_id))

    elif request.method == 'DELETE':
        params = request.get_json()

        if params is None:
            abort(400)
            return

        # Throws key error and responds 403 if something is missing
        recipe_id = params['id']

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute('''PRAGMA FOREIGN_KEYS=ON''')
            cur.execute('''DELETE FROM recipes WHERE id = ?''', [recipe_id])
            return 'OK\n'


@app.route('/api/ingredient', methods=['POST', 'GET'])
def add_ingredient():
    if request.method == 'POST':
        params = request.get_json()
        ingr_name = params['name']

        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute('''PRAGMA FOREIGN_KEYS=ON''')
            cur.execute('''SELECT * FROM ingredients WHERE name = ?''', [ingr_name])
            r = cur.fetchone()

            if r is not None:
                # Ingredient already exists
                abort(409)
                return

            cur.execute('''INSERT INTO ingredients VALUES (NULL, ?)''', [ingr_name])
            ingr_id = cur.lastrowid
            con.commit()

            cur.execute('''SELECT * FROM ingredients WHERE id = ?''', [ingr_id])
            row = cur.fetchone()
            return jsonify(dict_from_row(row))
    elif request.method == 'GET':
        name = request.args.get('name')

        if name is None:
            abort(400)
            return

        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute('''PRAGMA FOREIGN_KEYS=ON''')
            cur.execute('''SELECT * FROM ingredients WHERE name = ?''', [name])
            row = cur.fetchone()

            if row is None:
                return jsonify({})

            return jsonify(dict_from_row(row))


@app.route('/api/ingredient/<int:ingr_id>', methods=['GET'])
def get_ingredient(ingr_id):
    if ingr_id is None:
        abort(400)
        return

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('''PRAGMA FOREIGN_KEYS=ON''')
        cur.execute('''SELECT * FROM ingredients WHERE id=?''', [ingr_id])

        row = cur.fetchone()
        if row is None:
            abort(404)
            return

        return jsonify(dict_from_row(row))


@app.route('/api/latest', methods=['GET'])
def get_latest():
    num_rows = 20
    try:
        param_rows = request.args.get('rows')
        if param_rows is not None:
            num_rows = int(num_rows)
            if num_rows < 1:
                num_rows = 1
            if num_rows > 100:
                num_rows = 100
    except ValueError:
        abort(400)
        return

    with sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('''SELECT recipes.id,name, created, path as "image" FROM recipes 
                      INNER JOIN pictures p ON recipes.pic_id = p.id ORDER BY created''')
        return jsonify([dict_from_row(r) for r in cur.fetchmany(num_rows)])


if __name__ == '__main__':
    app.run()
