def to_update_dict(model) -> dict:
    if model is None:
        return {}
    # Pydantic v2
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    # Pydantic v1
    return model.dict(exclude_unset=True)
