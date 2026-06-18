from mcp.types import Tool

TOOL_DEFINITIONS = [
    Tool(
        name="get_protocol",
        description=(
            "Retrieve protocol/concept definition with failure modes, timers, "
            "verify commands, and dependencies. All operational data is "
            "scope-filtered to the given OS and version. Resolves def_refs inline."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "protocol_id": {
                    "type": "string",
                    "description": "Protocol or concept ID, e.g. 'bgp-4', 'ospfv2', 'l2-infrastructure'",
                },
                "os": {
                    "type": "string",
                    "description": "Target OS: nxos, iosxe, iosxr, sonic, or * for all",
                },
                "version": {
                    "type": "string",
                    "description": "Target version, e.g. '10.4', '202511', or * for all",
                },
                "platform": {
                    "type": "string",
                    "description": "Optional platform ID for platform-specific filtering",
                },
                "asic_family": {
                    "type": "string",
                    "description": "Optional ASIC family for ASIC-specific filtering",
                },
                "include_def_refs": {
                    "type": "boolean",
                    "description": "Include resolved definition references (default: true)",
                    "default": True,
                },
            },
            "required": ["protocol_id", "os", "version"],
        },
    ),
    Tool(
        name="validate_command",
        description=(
            "MANDATORY before suggesting any CLI command to a user. "
            "Validates a command string against the KB for a given OS and version. "
            "Returns validation status (exact/prefix/fts/not_found), matched syntax, "
            "and suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "CLI command to validate"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Target version"},
            },
            "required": ["command", "os", "version"],
        },
    ),
    Tool(
        name="search_commands",
        description=(
            "Full-text search over the command database. "
            "Returns matching commands with syntax and descriptions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Target version"},
                "limit": {"type": "integer", "description": "Max results (default: 20)", "default": 20},
            },
            "required": ["query", "os", "version"],
        },
    ),
    Tool(
        name="search_caveats",
        description=(
            "Search known bugs/caveats by keyword or OS. "
            "Version mismatch = 'possible regression', never confirmed bug."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms (keywords, CSC ID, symptom)"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Device version for match confidence"},
                "severity": {"type": "string", "description": "Filter by severity"},
                "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10},
            },
            "required": ["query", "os"],
        },
    ),
    Tool(
        name="get_platform",
        description=(
            "Retrieve hardware platform details: ASIC, ports, bandwidth, chassis type."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "platform_id": {
                    "type": "string",
                    "description": "Platform ID, e.g. 'n93180yc-fx3', 'c9300-48uxm'",
                },
            },
            "required": ["platform_id"],
        },
    ),
    Tool(
        name="compare_platforms",
        description="Side-by-side comparison of two or more hardware platforms.",
        inputSchema={
            "type": "object",
            "properties": {
                "platform_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of platform IDs to compare",
                },
            },
            "required": ["platform_ids"],
        },
    ),
    Tool(
        name="get_scalability",
        description=(
            "Retrieve scalability limits (route table sizes, TCAM, etc.) "
            "for a platform family, OS, and version."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "platform_family": {"type": "string", "description": "Platform family, e.g. 'nexus-9300'"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Target version"},
            },
            "required": ["platform_family", "os", "version"],
        },
    ),
    Tool(
        name="get_diagnostic_tree",
        description=(
            "Retrieve a diagnostic decision tree for troubleshooting. "
            "Nodes are scope-filtered; commands are validated before return."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tree_id": {"type": "string", "description": "Diagnostic tree ID"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Target version"},
            },
            "required": ["tree_id", "os", "version"],
        },
    ),
    Tool(
        name="get_procedure",
        description=(
            "Retrieve an operational procedure with validated commands per step."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "procedure_id": {"type": "string", "description": "Procedure ID"},
                "os": {"type": "string", "description": "Target OS"},
                "version": {"type": "string", "description": "Target version"},
            },
            "required": ["procedure_id", "os", "version"],
        },
    ),
    Tool(
        name="get_human_error",
        description="Retrieve a known operator mistake pattern with detection commands.",
        inputSchema={
            "type": "object",
            "properties": {
                "error_id": {"type": "string", "description": "Human error ID"},
                "os": {"type": "string", "description": "Target OS"},
            },
            "required": ["error_id", "os"],
        },
    ),
    Tool(
        name="search_human_errors",
        description="Search common operator mistakes by symptoms.",
        inputSchema={
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Symptom descriptions to match against",
                },
                "os": {"type": "string", "description": "Target OS"},
            },
            "required": ["symptoms", "os"],
        },
    ),
    Tool(
        name="open_case",
        description=(
            "Open a new troubleshooting case. Starts at the triage phase."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "symptom": {"type": "string", "description": "Problem description"},
                "os": {"type": "string", "description": "Device OS"},
                "version": {"type": "string", "description": "Device version"},
                "platform": {"type": "string", "description": "Device platform ID"},
            },
            "required": ["symptom", "os", "version"],
        },
    ),
    Tool(
        name="get_case",
        description="Read current state of a troubleshooting case.",
        inputSchema={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID (e.g. '001')"},
            },
            "required": ["case_id"],
        },
    ),
    Tool(
        name="advance_phase",
        description=(
            "Advance a case to the next methodology phase. "
            "Enforces phase sequencing: cannot skip phases. "
            "Resolve requires confirmed root cause."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID"},
                "current_phase": {
                    "type": "string",
                    "description": "Phase being completed (must match case's current phase)",
                },
                "output": {
                    "type": "string",
                    "description": "Phase findings/conclusion to record",
                },
            },
            "required": ["case_id", "current_phase", "output"],
        },
    ),
    Tool(
        name="check_kb_coverage",
        description=(
            "Check whether a topic is covered in the knowledge base. "
            "Returns matching protocols, diagnostics, procedures, and human errors."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic to search for"},
                "os": {"type": "string", "description": "Target OS (or * for all)"},
            },
            "required": ["topic", "os"],
        },
    ),
    Tool(
        name="get_best_practices",
        description="Retrieve the best-practices document index for an OS.",
        inputSchema={
            "type": "object",
            "properties": {
                "os": {"type": "string", "description": "Target OS"},
            },
            "required": ["os"],
        },
    ),
    Tool(
        name="get_interpretation_rule",
        description=(
            "Retrieve an interpretation rule — experience-based guidance for "
            "correctly reading command output, counters, logs, or state displays. "
            "Explains what a value actually means vs. what it appears to mean."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "rule_id": {"type": "string", "description": "Interpretation rule ID"},
                "os": {"type": "string", "description": "Target OS"},
            },
            "required": ["rule_id", "os"],
        },
    ),
    Tool(
        name="search_interpretation_rules",
        description=(
            "Search interpretation rules by keyword. Finds rules about counter "
            "interpretation, log analysis, expected behavior, and output semantics."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms (e.g. 'CRC counters', 'BGP CPU', 'log causation')"},
                "os": {"type": "string", "description": "Target OS"},
                "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10},
            },
            "required": ["query", "os"],
        },
    ),
]
