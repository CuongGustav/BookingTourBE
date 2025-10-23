from src import create_app
from src.extension import db
from sqlalchemy.sql import text

app = create_app()

@app.route("/test-db")
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "Kết nối MySQL thành công!"
    except Exception as e:
        return f"Lỗi kết nối DB: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
