from http import HTTPStatus

from flask import Flask, Response, redirect, render_template, request, url_for

from redcode import config, errors, machine


__all__ = ['create_app']


app = create_app = Flask(__name__)
INSTANCE = machine.Machine()


@app.route('/battle')
def battle(instance: machine.Machine = INSTANCE):
    return render_template(
        'battle.html',
        processes=instance.processes,
        memory=instance.memory,
        memory_size=config.MEMORY_SIZE,
    )


@app.route('/tick')
def tick():
    INSTANCE.turn()
    return redirect(url_for('battle'))


@app.route('/reset')
def reset():
    INSTANCE.reset()
    return redirect(url_for('battle'))


def bad_code_sent(e: ExceptionGroup):
    exceptions = e.exceptions
    return (
        render_template('partials/errors.html', errors=exceptions),
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )


@app.route('/test_run', methods=['POST'])
def test_run():
    player_name = request.form['player-name'] or 'Test'
    code = request.form['code']

    instance = machine.Machine(memory_size=128)
    try:
        instance.load_code(code, player_name)
    except ExceptionGroup as e:
        return bad_code_sent(e)

    return render_template(
        'battle.html',
        processes=instance.processes,
        memory=instance.memory,
        memory_size=len(instance.memory),
    )


@app.route('/code')
def code():
    return render_template('code.html')


@app.route('/code/send', methods=['POST'])
def code_send(instance: machine.Machine = INSTANCE):
    player_name = request.form['player-name']
    code = request.form['code']
    try:
        instance.load_code(code, player_name)
    except ExceptionGroup as e:
        return bad_code_sent(e)

    resp = Response()
    resp.headers['HX-Redirect'] = '/battle'
    return resp


def memory_safe_read(index: None = None, instance: machine.Machine = INSTANCE):
    print(f"Reading {index=}")
    try:
        return instance.memory[index]
    except errors.RedcodeRuntimeError:
        return "???"


app.jinja_env.filters['memory_safe_read'] = memory_safe_read

if __name__ == '__main__':
    app.run(debug=True)
