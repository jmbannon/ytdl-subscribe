from ytdl_sub.script.script import Script


def single_variable_output(script: str):
    output = (
        Script(
            {
                "output": script,
            }
        )
        .resolve(update=True)
        .get("output")
        .native
    )
    return output
