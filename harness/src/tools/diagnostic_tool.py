from harness.src.retrieval.scope_filter import Scope, matches_scope, filter_scoped
from harness.src.tools.base import ToolContext, wrap_result


class DiagnosticTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_diagnostic_tree(self, tree_id: str, os: str,
                            version: str) -> dict:
        doc = self._ctx.loader.get_diagnostic(tree_id)
        if doc is None:
            return wrap_result(
                "get_diagnostic_tree",
                {"tree_id": tree_id, "os": os, "version": version},
                None,
                kb_coverage="not_indexed",
            )

        scope = Scope(os=os, version=version)
        nodes = []
        for node in doc.get("nodes", []):
            node_scope = node.get("scope")
            if node_scope and not matches_scope(node_scope, scope):
                continue

            filtered_node = {
                "node_id": node.get("node_id"),
                "node_type": node.get("node_type"),
            }

            if node.get("node_type") == "branch":
                filtered_node["question"] = node.get("question")
                filtered_node["branches"] = node.get("branches", {})
                filtered_node["commands"] = self._validate_commands(
                    filter_scoped(node.get("commands", []), scope), os, version
                )
            elif node.get("node_type") == "leaf":
                filtered_node["finding"] = node.get("finding")
                filtered_node["action"] = node.get("action")
                cmds = node.get("commands", [])
                if cmds:
                    filtered_node["commands"] = self._validate_commands(
                        filter_scoped(cmds, scope), os, version
                    )

            nodes.append(filtered_node)

        data = {
            "tree_id": doc.get("tree_id"),
            "display_name": doc.get("display_name"),
            "entry_symptom": doc.get("entry_symptom"),
            "nodes": nodes,
        }
        return wrap_result(
            "get_diagnostic_tree",
            {"tree_id": tree_id, "os": os, "version": version},
            data,
        )

    def _validate_commands(self, commands: list[dict], os: str,
                           version: str) -> list[dict]:
        result = []
        for cmd in commands:
            syntax = cmd.get("command", "")
            validation = self._ctx.cmd_validator.validate(syntax, os, version)
            entry = dict(cmd)
            entry["validation"] = validation.to_dict()
            result.append(entry)
        return result
