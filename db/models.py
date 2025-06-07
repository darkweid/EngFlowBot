from datetime import date, datetime, time
from typing import List, Optional
from sqlalchemy import (Integer, String, Date, DateTime, Time, Boolean, ForeignKey,
                        ForeignKeyConstraint, Index, BigInteger)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for index, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or index < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class TestingExercise(Base):
    __tablename__ = 'testing_exercises'
    section: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    subsection: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    test: Mapped[str] = mapped_column(String(256), nullable=False)
    answer: Mapped[str] = mapped_column(String(256), nullable=False)


class NewWords(Base):
    __tablename__ = 'new_words'
    section: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    subsection: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    russian: Mapped[str] = mapped_column(String(256), nullable=False)
    english: Mapped[str] = mapped_column(String(256), nullable=False)
    user_words: Mapped[List["UserWordsLearning"]] = relationship(
        back_populates="new_word"
    )


class UserWordsLearning(Base):
    __tablename__ = 'user_words_learning'
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey('users.user_id', ondelete='CASCADE'),
                                         primary_key=True, nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False, index=True)
    subsection: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False, index=True)
    exercise_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    add_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    new_word: Mapped["NewWords"] = relationship(
        back_populates="user_words"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ['section', 'subsection', 'exercise_id'],
            ['new_words.section', 'new_words.subsection', 'new_words.id'],
            ondelete='CASCADE'
        ),
    )


Index('ix_user_section', UserWordsLearning.user_id, UserWordsLearning.section,
      UserWordsLearning.subsection)


class UserProgress(Base):
    __tablename__ = 'user_progress'
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey('users.user_id', ondelete='CASCADE'),
                                         primary_key=True,
                                         nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    exercise_section: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    exercise_subsection: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration_date: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(256))
    tg_login: Mapped[Optional[str]] = mapped_column(String(32))
    points: Mapped[int] = mapped_column(Integer, default=0)
    reminder_time: Mapped[Optional[time]] = mapped_column(Time)
    time_zone: Mapped[Optional[str]] = mapped_column(String)


class DailyStatistics(Base):
    __tablename__ = 'daily_statistics'
    date: Mapped[date] = mapped_column(Date, primary_key=True, nullable=False)
    total_testing_exercises: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_new_words: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_irregular_verbs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


Index('ix_daily_statistics_date', DailyStatistics.date)
