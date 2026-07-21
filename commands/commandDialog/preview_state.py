def cabinet_prefix(input_id, parameter_names):
    for name in sorted(parameter_names, key=len, reverse=True):
        if not input_id.endswith(name):
            continue
        prefix = input_id[: -len(name)]
        if prefix.endswith("_"):
            return prefix
    return None


class PreviewSessionState:
    def __init__(self):
        self.reset()

    def mark_dirty(self, prefix):
        if not prefix:
            return
        self._touched_prefixes.add(prefix)
        if self.live_preview:
            self._preview_prefixes.add(prefix)

    def request_update(self, prefix):
        self.mark_dirty(prefix)
        self._requested_prefixes.add(prefix)

    def preview_prefixes(self):
        return self._preview_prefixes | self._requested_prefixes

    def execute_prefixes(self):
        return set(self._touched_prefixes)

    def mark_preview_succeeded(self, prefixes):
        self._preview_prefixes.difference_update(prefixes)
        self._requested_prefixes.difference_update(prefixes)

    def discard(self, prefixes):
        self._preview_prefixes.difference_update(prefixes)
        self._requested_prefixes.difference_update(prefixes)
        self._touched_prefixes.difference_update(prefixes)

    def reset(self):
        self.live_preview = False
        self._preview_prefixes = set()
        self._requested_prefixes = set()
        self._touched_prefixes = set()


session_state = PreviewSessionState()