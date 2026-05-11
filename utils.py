def parse_bitable_fields(record: dict) -> dict:
    """将 Bitable 的 field 数组格式转为普通 dict"""
    fields = {}
    for k, v in record.get("fields", {}).items():
        if isinstance(v, list) and v:
            fields[k] = v[0].get("text", v[0]) if isinstance(v[0], dict) else v[0]
        else:
            fields[k] = v
    return fields
