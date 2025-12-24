from src.extension import ma
from src.model.model_favorite import Favorites

class FavoriteSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Favorites
        load_instance = True 
        include_fk = True 

    favorite_id = ma.auto_field()
    account_id = ma.auto_field()
    tour_id = ma.auto_field()

favorite_schema = FavoriteSchema()