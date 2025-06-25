# backend/app/api/__init__.py

# 这行代码的作用是，当其他文件导入`app.api`这个包时，
# 我们直接把`meetings.py`里面的`router`对象暴露出去。
from .meetings import router