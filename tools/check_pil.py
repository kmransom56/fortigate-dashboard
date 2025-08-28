try:
    from PIL import Image  # noqa: F401
    print("PIL OK")
except Exception as e:
    print(f"PIL error: {e}")
    raise
