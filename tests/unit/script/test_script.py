from ytdl_sub.script.script import Script
from ytdl_sub.script.types.map import ResolvedMap
from ytdl_sub.script.types.resolvable import String


class TestScript:
    def test_pre_resolved(self):
        assert Script(
            {
                "%custom_func": "return {[$0, $1]}",
                "aa": "a",
                "bb": "b",
                "cc": "{%custom_func(aa, bb)}",
            }
        ).resolve(resolved={"bb": String("bb_override")}) == {
            "aa": String("a"),
            "bb": String("bb_override"),
            "cc": String('return ["a", "bb_override"]'),
        }

    def test_partial_resolve(self):
        assert Script(
            {
                "%custom_func": "return {[$0, $1]}",
                "aa": "a",
                "bb": "b",
                "cc": "{%custom_func(aa, bb)}",
            }
        ).resolve(unresolvable={"bb"}) == {"aa": String("a")}

    def test_partial_update_script(self):
        # to be resolved later
        entry_map = ResolvedMap({String("title"): String("the title")})

        script = Script(
            {
                "entry": "{%throw('entry has not been populated yet')}",
                "title": "{%map_get(entry, 'title')}",
                "override": "hi",
                "resolved_override": "{override} mom",
            }
        )

        script.resolve(unresolvable={"entry"}, update=True)
        assert script.get("override") == String("hi")
        assert script.get("resolved_override") == String("hi mom")

        script.add(
            {
                "new_variable_titlecase": "{%titlecase(new_variable_upper)}",
                "new_variable": "{resolved_override} {title}",
                "new_variable_upper": "{%upper(new_variable)}",
            }
        ).resolve(resolved={"entry": entry_map}, update=True)

        assert script.get("title") == String("the title")
        assert script.get("new_variable") == String("hi mom the title")
        assert script.get("new_variable_upper") == String("HI MOM THE TITLE")
        assert script.get("new_variable_titlecase") == String("Hi Mom The Title")
        assert script.get("entry") == entry_map
