import logging 
from typing import Optional, List

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.engine import AsyncSessionLocal
from database.models import User, Category, Furniture, FurniturePhoto


class CrudUser:
    def __init__(self):
        self.session = AsyncSessionLocal

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        async with self.session() as session:
            try:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при получении пользователя по Telegram ID:', exc)
                return None

    async def create_user(self, telegram_id: int, username: str | None, firstname: str | None, lastname: str | None) -> User:
        async with self.session() as session:
            try:
                count_stmt = select(func.count()).select_from(User)
                count_result = await session.execute(count_stmt)
                is_first_user = count_result.scalar() == 0

                new_user = User(
                    telegram_id=telegram_id,
                    username=username,
                    firstname=firstname,
                    lastname=lastname,
                    is_admin=is_first_user  
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                return new_user
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при создании пользователя:', exc)
                raise exc


class CrudCategory:
    def __init__(self):
        self.session = AsyncSessionLocal

    async def get_all_categories(self) -> List[Category]:
        async with self.session() as session:
            try:
                stmt = select(Category)
                result = await session.execute(stmt)
                all_categories = result.scalars().all()
                return list(all_categories) if all_categories else []
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при получении всех категорий:', exc)
                return []

    async def create_category(self, name: str, description: str) -> bool:
        async with self.session() as session:
            try:
                new_cat = Category(name=name, description=description)
                session.add(new_cat)
                await session.commit()
                logging.info(f'Создана категория {name}')
                return True
            except IntegrityError as exc:
                await session.rollback()
                logging.error(f'IntegrityError при создании категории. Тип: {exc}')
                return False
            except SQLAlchemyError as exc:
                await session.rollback()
                logging.error(f'SQLAlchemyError при создании категории. Тип: {exc}')
                return False


    async def check_category_by_name(self, name: str) -> bool:
        async with self.session() as session:
            try:
                stmt = select(Category).where(Category.name == name)
                result = await session.execute(stmt)
                category = result.scalar_one_or_none()
                return category is not None
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при проверке существования категории по имени:', exc)
                return False


    async def delete_category_by_name(self, name: str) -> bool:
        async with self.session() as session:
            try:
                stmt = delete(Category).where(Category.name == name)
                await session.execute(stmt)
                await session.commit()
                return True
            except SQLAlchemyError as exc:
                await session.rollback()
                logging.exception('Ошибка при удалении категории:', exc)
                return False


class CrudFurniture:
    def __init__(self):
        self.session = AsyncSessionLocal

    async def get_furniture_by_category(self, category_name: str) -> List[Furniture]:
        async with self.session() as session:
            try:
                stmt = select(Furniture).where(Furniture.category_name == category_name)
                result = await session.execute(stmt)
                items = result.scalars().all()
                return list(items) if items else []
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при получении мебели по категории:', exc)
                return []

    async def get_photos_by_furniture_id(self, furniture_id: int) -> List[FurniturePhoto]:
        async with self.session() as session:
            try:
                stmt = select(FurniturePhoto).where(FurniturePhoto.furniture_id == furniture_id)
                result = await session.execute(stmt)
                photos = result.scalars().all()
                return list(photos) if photos else []
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при получении фотографий мебели:', exc)
                return []


    async def create_furniture(self, description: str, category: str, country: str, kitchen_type: Optional[str] = None) -> Optional[Furniture]:
        async with self.session() as session:
            try:
                new_item = Furniture(
                    description=description,
                    category_name=category,
                    country_origin=country,
                    kitchen_type=kitchen_type
                )
                session.add(new_item)
                await session.commit()
                await session.refresh(new_item)
                return new_item
            except SQLAlchemyError as exc:
                await session.rollback()
                logging.exception('Ошибка при сохранении мебели в БД:', exc)
                return None


    async def add_photos_to_furniture(self, furniture_id: int, photos: list[str]) -> bool:
        async with self.session() as session:
            try:
                for file_id in photos:
                    new_photo = FurniturePhoto(
                        furniture_id=furniture_id,
                        file_id=file_id
                    )
                    session.add(new_photo)
                await session.commit()
                return True
            except SQLAlchemyError as exc:
                await session.rollback()
                logging.exception('Ошибка при сохранении фотографий мебели:', exc)
                return False


    async def get_all_furniture(self) -> list[Furniture]:
        async with self.session() as session:
            try:
                stmt = select(Furniture)
                result = await session.execute(stmt)
                return list(result.scalars().all())
            except SQLAlchemyError as exc:
                logging.exception('Ошибка при получении всей мебели:', exc)
                return []

    async def delete_furniture_by_id(self, furniture_id: int) -> bool:
        async with self.session() as session:
            try:
                stmt = delete(Furniture).where(Furniture.id == furniture_id)
                await session.execute(stmt)
                await session.commit()
                return True
            except SQLAlchemyError as exc:
                await session.rollback()
                logging.exception('Ошибка при удалении мебели:', exc)
                return False


