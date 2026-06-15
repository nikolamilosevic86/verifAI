import modal

_cls = None


def _get_cls():
    global _cls
    if _cls is None:
        _cls = modal.Cls.from_name("verifai-mistral", "MistralModel")
    return _cls


def modal_stream(prompt: str, temperature: float):
    instance = _get_cls()()
    yield from instance.stream_generate.remote_gen(prompt, temperature)
