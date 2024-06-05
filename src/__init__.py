from flask import Flask, Response, redirect, render_template, request, url_for

from redcode import config, errors, machine


__all__ = ['create_app']


app = create_app = Flask(__name__)
instance = machine.Machine()


@app.route('/battle')
def battle():
    return render_template(
        'battle.html',
        processes=instance.processes,
        memory=instance.memory,
        memory_size=config.MEMORY_SIZE,
    )


@app.route('/tick')
def tick():
    instance.turn()
    return redirect(url_for('battle'))


@app.route('/code')
def code():
    return render_template(
        'code.html',
    )


@app.route('/code/send', methods=['POST'])
def code_send():
    player_name = request.form['player-name']
    code = request.form['code']
    try:
        instance.load_code(code, player_name)
    except ExceptionGroup as e:
        return render_template('partials/errors.html', errors=e.exceptions)

    resp = Response("Foo bar baz")
    resp.headers['HX-Redirect'] = '/battle'
    return resp


def memory_safe_read(index):
    try:
        return instance.memory[index]
    except errors.RedcodeRuntimeError:
        return "???"


app.jinja_env.filters['memory_safe_read'] = memory_safe_read

if __name__ == '__main__':
    app.run(debug=True)
