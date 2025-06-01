import random
from datetime import datetime, date, timedelta

# from sqlalchemy.future import select
from sqlalchemy import select, func, update, delete, not_, desc, distinct
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from db.init import engine
from db.models import (TestingExercise, NewWords, UserProgress, User, UserWordsLearning,
                       DailyStatistics)
from loggers import get_logger

logger = get_logger(__name__)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()

    async def close(self):
        await self.db.close()


class TestingManager(DatabaseManager):
    async def add_testing_exercise(self, section, subsection, test, answer):
        async with self.db as session:
            async with session.begin():
                max_id = await session.execute(
                    select(func.max(TestingExercise.id)).filter_by(section=section, subsection=subsection))
                max_id = max_id.scalar() or 0
                next_id = max_id + 1

                exercise = TestingExercise(section=section, subsection=subsection, id=next_id, test=test,
                                           answer=answer.replace(chr(160), ''))
                session.add(exercise)

    async def get_testing_exercises(self, subsection: str):
        async with self.db as session:
            res = await session.execute(
                select(TestingExercise).filter_by(subsection=subsection).order_by(TestingExercise.id))
            exercises = res.scalars().all()
            result = ''
            for exercise in exercises:
                result += f'{exercise.id}) {exercise.test}. Ответ: {exercise.answer}\n\n'
            return result

    async def get_count_testing_exercises_in_subsection(self, section: str, subsection: str):
        async with self.db as session:
            count_exercises_in_subsection = (await session.execute(
                select(func.count()).select_from(TestingExercise).where(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection))).scalar()
            return count_exercises_in_subsection

    async def get_random_testing_exercise(self, section: str, subsection: str, user_id: int):
        async with self.db as session:
            # Подзапрос для получения ID упражнений, которые пользователь уже выполнил успешно
            subquery = (select(UserProgress.exercise_id).filter(
                UserProgress.user_id == user_id,
                UserProgress.exercise_section == section,
                UserProgress.exercise_subsection == subsection,
                UserProgress.success == True)).subquery()

            # Основной запрос для получения упражнений, которые пользователь еще не выполнял успешно
            stmt = (
                select(TestingExercise)
                .filter(
                    TestingExercise.section == section,
                    TestingExercise.subsection == subsection,
                    TestingExercise.id.not_in(subquery)
                )
            )

            result = await session.execute(stmt)
            exercises = result.scalars().all()

            if not exercises:
                return None
            result = random.choice(exercises)
            return result.test, result.answer, result.id

    async def get_section_names(self):
        async with self.db as session:
            res = await session.execute(
                select(distinct(TestingExercise.section)).order_by(TestingExercise.section))
            subsections = res.scalars().all()
            return subsections

    async def get_subsection_names(self, section: str):
        async with self.db as session:
            res = await session.execute(
                select(distinct(TestingExercise.subsection)).filter_by(section=section).order_by(
                    TestingExercise.subsection))
            subsections = res.scalars().all()
            return subsections

    async def edit_testing_exercise(self, section, subsection, test, answer, index):
        async with self.db as session:
            async with session.begin():
                await session.execute(
                    update(TestingExercise).where(TestingExercise.section == section,
                                                  TestingExercise.subsection == subsection,
                                                  TestingExercise.id == index).values(test=test, answer=answer))

    async def delete_testing_exercise(self, section, subsection, index):
        async with self.db as session:
            async with session.begin():
                await session.execute(
                    delete(TestingExercise).where(TestingExercise.section == section,
                                                  TestingExercise.subsection == subsection,
                                                  TestingExercise.id == index))


class NewWordsExerciseManager(DatabaseManager):
    async def add_new_words_exercise(self, section, subsection, russian, english):
        async with self.db as session:
            async with session.begin():
                max_id = await session.execute(
                    select(func.max(NewWords.id)).filter_by(section=section, subsection=subsection))
                max_id = max_id.scalar() or 0
                next_id = max_id + 1

                exercise = NewWords(section=section, subsection=subsection, id=next_id, russian=russian,
                                    english=english)
                session.add(exercise)

    async def delete_new_words_exercise(self, section, subsection, index):
        async with self.db as session:
            async with session.begin():
                await session.execute(
                    delete(NewWords).where(NewWords.section == section,
                                           NewWords.subsection == subsection,
                                           NewWords.id == index))

    async def edit_new_words_exercise(self, section, subsection, russian, english, index):
        async with self.db as session:
            async with session.begin():
                await session.execute(
                    update(NewWords).where(NewWords.section == section,
                                           NewWords.subsection == subsection,
                                           NewWords.id == index).values(russian=russian, english=english))

    async def get_count_new_words_exercises_in_subsection(self, section: str, subsection: str):
        async with self.db as session:
            count_exercises_in_subsection = (await session.execute(
                select(func.count()).select_from(NewWords).where(
                    NewWords.section == section,
                    NewWords.subsection == subsection))).scalar()
            return count_exercises_in_subsection

    async def get_new_words_exercises(self, subsection: str):
        async with self.db as session:
            if isinstance(subsection, int):
                subsection = str(subsection)

            res = await session.execute(
                select(NewWords).filter_by(subsection=subsection).order_by(NewWords.id))
            exercises = res.scalars().all()
            result = ''
            for exercise in exercises:
                result += f'{exercise.id}) {exercise.russian} – {exercise.english}\n'
            return result

    async def get_subsection_names(self, section: str):
        async with self.db as session:
            res = await session.execute(
                select(distinct(NewWords.subsection)).filter_by(section=section).order_by(NewWords.subsection))
            subsections = res.scalars().all()
            return subsections


class UserWordsLearningManager(DatabaseManager):
    ACTIVE_LEARNING_RATE = 3
    LEARNED_RATE = 5

    async def get_random_word_exercise(self, user_id: int) -> dict:
        async with self.db as session:
            words_to_learn_today = (
                select(UserWordsLearning)
                .filter(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.next_review_date <= date.today()
                )).options(joinedload(UserWordsLearning.new_word))

            words_to_learn_today = (await session.execute(words_to_learn_today)).scalars().all()
            if not words_to_learn_today:
                return None

            exercise = random.choice(words_to_learn_today)

            all_words = (
                select(UserWordsLearning)
                .filter(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.section == exercise.new_word.section,
                    UserWordsLearning.subsection == exercise.new_word.subsection
                )).options(joinedload(UserWordsLearning.new_word))
            all_words = (await session.execute(all_words)).scalars().all()

        options = [word.new_word.russian.capitalize() for word in all_words if
                   word.new_word.russian != exercise.new_word.russian]
        if len(options) < 3:
            all_words = (
                select(UserWordsLearning)
                .filter(
                    UserWordsLearning.user_id == user_id,
                )).options(joinedload(UserWordsLearning.new_word))

            all_words = (await session.execute(all_words)).scalars().all()
            options = [word.new_word.russian.capitalize() for word in all_words if
                       word.new_word.russian != exercise.new_word.russian]

        options = random.sample(options, 3)

        return {
            'russian': exercise.new_word.russian.capitalize(),
            'english': exercise.new_word.english.capitalize(),
            'section': exercise.new_word.section,
            'subsection': exercise.new_word.subsection,
            'exercise_id': exercise.exercise_id,
            'options': options
        }

    async def get_count_active_learning_exercises(self, user_id: int) -> int:
        async with self.db as session:
            count = (await session.execute(
                select(func.count(UserWordsLearning.exercise_id)).where(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.success <= self.ACTIVE_LEARNING_RATE))).scalar()
            return count

    async def get_count_learned_exercises(self, user_id: int) -> int:
        async with self.db as session:
            count = (await session.execute(
                select(func.count(UserWordsLearning.exercise_id)).where(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.success >= self.LEARNED_RATE))).scalar()
            return count

    async def get_count_all_exercises_by_user(self, user_id: int) -> int:
        async with self.db as session:
            count = (await session.execute(
                select(func.count(UserWordsLearning.exercise_id)).where(
                    UserWordsLearning.user_id == user_id))).scalar()
            return count

    async def get_count_all_exercises_for_today_by_user(self, user_id: int) -> int:
        async with self.db as session:
            count = (await session.execute(
                select(func.count(UserWordsLearning.exercise_id)).where(
                    UserWordsLearning.user_id == user_id,
                    UserWordsLearning.next_review_date <= date.today()))).scalar()
            return count

    async def get_added_subsections_by_user(self, user_id: int):
        async with self.db as session:
            result = await session.execute(
                select(distinct(UserWordsLearning.subsection))
                .filter(UserWordsLearning.user_id == user_id)
            )
            unique_subsections = result.scalars().all()
            return unique_subsections

    async def get_user_stats(self, user_id: int) -> dict:
        async with self.db as session:
            result = {}
            subsections = (await session.execute(
                select(distinct(UserWordsLearning.subsection))
                .filter(UserWordsLearning.user_id == user_id))).scalars().all()

            for subsection in subsections:
                learned = (await session.execute(
                    select(func.count(UserWordsLearning.exercise_id)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id,
                        UserWordsLearning.success >= self.LEARNED_RATE))).scalar()

                active_learning = (await session.execute(
                    select(func.count(UserWordsLearning.exercise_id)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id,
                        UserWordsLearning.success <= self.ACTIVE_LEARNING_RATE))).scalar()

                for_today_learning = (await session.execute(
                    select(func.count(UserWordsLearning.exercise_id)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id,
                        UserWordsLearning.next_review_date <= date.today()))).scalar()

                total_words_in_subsection = (await session.execute(
                    select(func.count(UserWordsLearning.exercise_id)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id))).scalar()

                total_success = (await session.execute(
                    select(func.sum(UserWordsLearning.success)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id))).scalar() or 0

                total_attempts = (await session.execute(
                    select(func.sum(UserWordsLearning.attempts)).where(
                        UserWordsLearning.subsection == subsection,
                        UserWordsLearning.user_id == user_id))).scalar() or 0

                if total_attempts > 0:
                    success_rate = (total_success / total_attempts) * 100
                else:
                    success_rate = 0

                result[subsection] = {
                    'learned': learned,
                    'for_today_learning': for_today_learning,
                    'active_learning': active_learning,
                    'total_words_in_subsection': total_words_in_subsection,
                    'success_rate': success_rate
                }
            return result

    async def set_progress(self, user_id: int, section: str, subsection: str, exercise_id: int, success: bool):
        async with self.db as session:
            async with session.begin():
                info = (await session.execute(select(UserWordsLearning).where(UserWordsLearning.user_id == user_id,
                                                                              UserWordsLearning.section == section,
                                                                              UserWordsLearning.subsection == subsection,
                                                                              UserWordsLearning.exercise_id == exercise_id))).scalars().first()
                next_review_date = date.today()
                success_value = info.success
                attempts = info.attempts + 1
                if success == True:
                    stmt = (update(User).where(User.user_id == user_id).values(points=User.points + 1))
                    await session.execute(stmt)
                    success_value += 1
                    next_review_date = await calculate_next_review_date(success_attempts=success_value,
                                                                        total_attempts=attempts)
                elif success == False:
                    stmt = (update(User).where(User.user_id == user_id).values(points=User.points - 1))
                    await session.execute(stmt)
                    next_review_date = date.today() + timedelta(days=1)

                await session.execute(
                    update(UserWordsLearning).where(UserWordsLearning.section == section,
                                                    UserWordsLearning.subsection == subsection,
                                                    UserWordsLearning.exercise_id == exercise_id).values(
                        success=success_value, next_review_date=next_review_date,
                        attempts=UserWordsLearning.attempts + 1
                    ))

    async def add_words_to_learning(self, section: str, subsection: str, user_id: int) -> None:
        async with self.db as session:
            async with session.begin():
                res = await session.execute(
                    select(NewWords).filter_by(subsection=subsection, section=section).order_by(NewWords.id))
                exercises = res.scalars().all()

                for exercise in exercises:
                    if isinstance(exercise, NewWords):
                        result = UserWordsLearning(
                            user_id=user_id,
                            section=section,
                            subsection=subsection,
                            exercise_id=exercise.id
                        )
                    session.add(result)

    async def admin_add_words_to_learning(self, russian: str, english: str, user_id: int) -> None:
        async with self.db as session:
            async with session.begin():
                max_id = await session.execute(
                    select(func.max(NewWords.id)).filter_by(section=str(user_id), subsection=str(user_id)))
                max_id = max_id.scalar() or 0
                next_id = max_id + 1
                exercise = NewWords(section=str(user_id), subsection=str(user_id), id=next_id, russian=russian,
                                    english=english)
                session.add(exercise)
                result = UserWordsLearning(
                    user_id=user_id,
                    section=str(user_id),
                    subsection=str(user_id),
                    exercise_id=next_id
                )
                session.add(result)


class UserProgressManager(DatabaseManager):
    async def mark_exercise_completed(self, user_id, exercise_type, subsection, section, exercise_id,
                                      success):
        async with self.db as session:
            async with session.begin():
                first_try = False
                stmt = (
                    update(UserProgress)
                    .where(
                        UserProgress.user_id == user_id,
                        UserProgress.exercise_type == exercise_type,
                        UserProgress.exercise_section == section,
                        UserProgress.exercise_subsection == subsection,
                        UserProgress.exercise_id == exercise_id
                    )
                    .values(
                        attempts=UserProgress.attempts + 1,
                        success=success,
                        date=date.today()
                    )
                )
                result = await session.execute(stmt)

                points = (1 if success else -1)
                stmt = (update(User).where(User.user_id == user_id).values(points=User.points + points))
                await session.execute(stmt)

                if result.rowcount == 0:
                    new_record = UserProgress(
                        user_id=user_id,
                        exercise_type=exercise_type,
                        exercise_section=section,
                        exercise_subsection=subsection,
                        exercise_id=exercise_id,
                        attempts=1,
                        success=success,
                        date=date.today()
                    )
                    session.add(new_record)
                    first_try = True

                return first_try

    async def get_counts_completed_exercises_testing(self, user_id, section, subsection):
        async with self.db as session:
            success_exercises_count = (await session.execute(
                select(func.count()).select_from(UserProgress).where(
                    UserProgress.user_id == user_id,
                    UserProgress.exercise_type == 'Testing',
                    UserProgress.exercise_section == section,
                    UserProgress.exercise_subsection == subsection,
                    UserProgress.success == True
                )
            )).scalar()

        first_try_success_exercises_count = (await session.execute(
            select(func.count()).select_from(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.exercise_type == 'Testing',
                UserProgress.exercise_section == section,
                UserProgress.exercise_subsection == subsection,
                UserProgress.success == True,
                UserProgress.attempts == 1
            )
        )).scalar()

        exercises_count = (await session.execute(
            select(func.count()).select_from(TestingExercise).where(
                TestingExercise.section == section,
                TestingExercise.subsection == subsection
            )
        )).scalar()

        return first_try_success_exercises_count, success_exercises_count, exercises_count

    async def get_activity_by_user(self, user_id: int, interval: int = 0):
        async with self.db as session:
            target_date = (datetime.utcnow() - timedelta(days=interval)).date()
            now = datetime.utcnow().date()
            result_testing = (await session.execute(
                select(func.count()).select_from(UserProgress).where(
                    UserProgress.exercise_type == 'Testing',
                    UserProgress.date >= target_date,
                    UserProgress.date <= now,
                    UserProgress.user_id == user_id))).scalar()

            result_new_words = (await session.execute(
                select(func.count()).select_from(UserProgress).where(
                    UserProgress.exercise_type == 'New words',
                    UserProgress.date >= target_date,
                    UserProgress.date <= now,
                    UserProgress.user_id == user_id))).scalar()

            result_irregular_verbs = (await session.execute(
                select(func.count()).select_from(UserProgress).where(
                    UserProgress.exercise_type == 'Irregular verbs',
                    UserProgress.date >= target_date,
                    func.date(UserProgress.date) <= now,
                    UserProgress.user_id == user_id))).scalar()
            if interval == 0:
                text = 'сегодня'
            elif interval == 7:
                text = 'последнюю неделю'
            elif interval == 30:
                text = 'последний месяц'
            info = f"""
Твоя статистика за <b>{text}</b>:
Тестирование: {result_testing}
Изучение новых слов: {result_new_words}
Неправильные глаголы: {result_irregular_verbs}
"""

            return info

    async def get_user_points(self, user_id: int):
        async with self.db as session:
            result_points = (await session.execute(
                select(User.points).select_from(User).where(
                    User.user_id == user_id))).scalar()

            return result_points

    async def get_user_rank_and_total(self, user_id: int, medals_rank: bool = False):
        async with self.db as session:
            async with session.begin():
                user_points = (await session.execute(
                    select(User.points).where(User.user_id == user_id))).scalar()

                higher_ranked_count = (await session.execute(
                    select(func.count()).select_from(User).where(User.points > user_points)
                )).scalar()

                total_users = (await session.execute(
                    select(func.count()).select_from(User)
                )).scalar()
                user_rank = higher_ranked_count + 1
                if medals_rank:
                    if user_rank == 1:
                        user_rank = '🥇'
                    elif user_rank == 2:
                        user_rank = '🥈'
                    elif user_rank == 3:
                        user_rank = '🥉'

                return user_rank, total_users

    async def get_all_users_ranks_and_points(self, medals_rank: bool = False):
        async with self.db as session:
            users = await session.execute(
                select(User.id, User.user_id, User.full_name, User.tg_login, User.points)
                .order_by(desc(User.points))
            )

            users = users.fetchall()

            users_with_ranks = []

            for rank, user in enumerate(users, start=1):
                if medals_rank:
                    if rank == 1:
                        rank = '🥇'
                    elif rank == 2:
                        rank = '🥈'
                    elif rank == 3:
                        rank = '🥉'

                users_with_ranks.append({
                    'rank': str(rank),
                    'user_id': str(user.user_id),
                    'full_name': user.full_name,
                    'tg_login': user.tg_login,
                    'points': str(user.points)
                })

            return users_with_ranks

    async def delete_progress_by_subsection(self, user_id, section, subsection):
        async with self.db as session:
            async with session.begin():
                await session.execute(delete(UserProgress).where(UserProgress.exercise_section == section,
                                                                 UserProgress.exercise_subsection == subsection,
                                                                 UserProgress.user_id == user_id))


class UserManager(DatabaseManager):
    async def add_user(self, user_id, full_name, tg_login):
        async with self.db as session:
            async with session.begin():
                result = await session.execute(select(User).filter(User.user_id == user_id))
                existing_user = result.scalar_one_or_none()
                if existing_user:
                    if existing_user.full_name != full_name or existing_user.tg_login != tg_login:
                        existing_user.full_name = full_name
                        existing_user.tg_login = tg_login
                        logger.info(f'User {user_id}:{full_name} information updated.')
                    else:
                        logger.info(f'User {user_id}:{full_name} already exists with the same information.')
                    return None

                user = User(
                    registration_date=datetime.utcnow(),
                    user_id=user_id,
                    full_name=full_name,
                    tg_login=tg_login,
                    reminder_time=None,
                    time_zone=None
                )
                session.add(user)
                logger.info(f'User {full_name} added successfully.')
                return None

    async def delete_user(self, user_id):
        async with self.db as session:
            async with session.begin():
                await session.execute(delete(User).where(User.user_id == user_id))

    async def set_timezone(self, user_id, timezone):
        async with self.db as session:
            async with session.begin():
                await session.execute(update(User).where(User.user_id == user_id).values(time_zone=timezone))

    async def set_reminder_time(self, user_id, time):
        async with self.db as session:
            async with session.begin():
                await session.execute(update(User).where(User.user_id == user_id).values(reminder_time=time))

    async def get_all_users(self):
        async with self.db as session:
            result = await session.execute(select(User).order_by(User.id))
            users = result.scalars().all()

            user_info = tuple(
                {
                    'id': user.id,
                    'user_id': user.user_id,
                    'full_name': user.full_name,
                    'tg_login': user.tg_login,
                    'registration_date': user.registration_date,
                    'points': user.points,
                    'reminder_time': user.reminder_time,
                    'time_zone': user.time_zone
                }
                for user in users
            )

            return user_info

    async def get_user(self, user_id: int):
        async with self.db as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalars().first()
            user_info = {
                'id': user.id,
                'user_id': user.user_id,
                'full_name': user.full_name,
                'tg_login': user.tg_login,
                'registration_date': user.registration_date,
                'points': user.points,
                'reminder_time': user.reminder_time,
                'time_zone': user.time_zone
            }

        return user_info

    async def get_user_info_text(self, user_id: int, admin: bool = True):
        async with self.db as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user:
                info = ''
                if admin:
                    info += f"""Имя: {user.full_name}
telegram: @{user.tg_login}
telegram id: {user.user_id}
Баллов: {user.points}\n"""

                info += f"""Дата регистрации: {user.registration_date.strftime('%d-%m-%Y | %H:%M UTC')}
Время напоминаний: {user.reminder_time if user.reminder_time else 'Не установлено'}
Часовой пояс: {user.time_zone if user.time_zone else 'Не установлен'}"""

            return info
        return None


class DailyStatisticsManager(DatabaseManager):
    async def update(self, update_type):
        async with self.db as session:
            async with session.begin():
                today = date.today()
                stats = (await session.execute(select(DailyStatistics).filter_by(date=today))).scalar_one_or_none()

                if not stats:
                    stats = DailyStatistics(date=today, total_new_words=0,
                                            total_testing_exercises=0,
                                            total_irregular_verbs=0,
                                            new_users=0)
                    session.add(stats)

                if update_type == 'new_words':
                    stats.total_new_words += 1
                elif update_type == 'testing_exercises':
                    stats.total_testing_exercises += 1
                elif update_type == 'irregular_verbs':
                    stats.total_irregular_verbs += 1
                elif update_type == 'new_user':
                    stats.new_users += 1

                await session.commit()

    async def get(self, start_date, end_date):
        async with self.db as session:
            result = await session.execute(
                select(
                    func.sum(DailyStatistics.total_testing_exercises).label("testing_exercises"),
                    func.sum(DailyStatistics.total_new_words).label("new_words"),
                    func.sum(DailyStatistics.total_irregular_verbs).label("irregular_verbs"),
                    func.sum(DailyStatistics.new_users).label("new_users")
                ).where(DailyStatistics.date >= start_date,
                        DailyStatistics.date <= end_date)
            )

            stats = result.one()

            return {
                "testing_exercises": stats.testing_exercises or 0,
                "new_words": stats.new_words or 0,
                "irregular_verbs": stats.irregular_verbs or 0,
                "new_users": stats.new_users or 0
            }


async def calculate_success_rate(success_attempts, total_attempts):
    if total_attempts == 0:
        return 0
    return success_attempts / total_attempts


async def calculate_next_interval(success_attempts, success_rate):
    base_interval = 1
    growth_factor = 1.7

    standard_interval = base_interval * (growth_factor ** success_attempts)

    # Коэффициент адаптации
    if success_rate >= 0.75:  # высокий успех, увеличиваем интервал
        adjustment_factor = 1 + (success_rate - 0.75) * 2
    elif success_rate < 0.75:  # низкий успех, уменьшаем интервал
        adjustment_factor = 1 - (0.75 - success_rate) * 2
    else:
        adjustment_factor = 1

    next_interval = standard_interval * adjustment_factor
    return next_interval


async def calculate_next_review_date(success_attempts, total_attempts):
    success_rate = await calculate_success_rate(success_attempts, total_attempts)
    next_interval_days = await calculate_next_interval(success_attempts, success_rate)
    next_review_date = date.today() + timedelta(days=next_interval_days)
    if next_review_date <= date.today():
        next_review_date = date.today() + timedelta(days=1)
    return next_review_date
