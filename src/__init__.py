from http import HTTPStatus

from flask import (
    Flask, Response, redirect, render_template, request, url_for,
)

from redcode import machine


__all__ = ['create_app']


app = create_app = Flask(__name__)
INSTANCE = machine.Machine(allow_single_process=True)
UPLOADED = {}


def render_battle(instance: machine.Machine):
    instance.run()
    assert instance.start_state is not None

    return render_template(
        'battle.html',
        processes=instance.start_state.processes,
        player_count=len(instance.start_state.processes),
        memory=instance.start_state.memory,
        memory_json=instance.start_state.memory.as_json(),
        memory_size=len(instance.memory),
        start_map=instance.start_map,
        ips=instance.start_state.ips,
        history=instance.json_history,
    )


def bad_code_sent(e: ExceptionGroup):
    exceptions = e.exceptions
    return (
        render_template('partials/errors.html', errors=exceptions),
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )


@app.route('/battle')
def battle(instance: machine.Machine = INSTANCE):
    instance = machine.Machine(allow_single_process=False)
    for player_name, code in UPLOADED.items():
        try:
            instance.load_code(code, player_name)
        except ExceptionGroup as e:
            return bad_code_sent(e)
    return render_battle(instance)


@app.route('/reset')
def reset(instance: machine.Machine = INSTANCE):
    instance.reset()
    return redirect(url_for('battle'))


@app.route('/test', methods=['POST'])
def test_run():
    player_name = request.form['player-name'] or 'Test'
    code = request.form['code']

    instance = machine.Machine(memory_size=128, allow_single_process=True)
    try:
        instance.load_code(code, player_name)
    except ExceptionGroup as e:
        return bad_code_sent(e)

    return render_battle(instance)


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

    if player_name in UPLOADED:
        return f'We already have code for {player_name}', HTTPStatus.CONFLICT

    UPLOADED[player_name] = code
    resp = Response()
    resp.headers['HX-Redirect'] = '/wait'
    return resp


if __name__ == '__main__':
    app.run(debug=True)
