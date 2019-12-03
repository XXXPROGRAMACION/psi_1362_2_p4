from django.db import models
from django.contrib.auth.models import User
from enum import IntEnum
from django.core.exceptions import ValidationError
from datetime import datetime
from datamodel import constants


class GameStatus(IntEnum):
    CREATED = 0
    ACTIVE = 1
    FINISHED = 2

    # Autor: Alejandro Pascual Pozo
    def to_string(game_status):
        if game_status == GameStatus.CREATED:
            return 'Created'
        elif game_status == GameStatus.ACTIVE:
            return 'Active'
        elif game_status == GameStatus.FINISHED:
            return 'Finished'
        else:
            return 'Error'


class Game(models.Model):
    cat_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='games_as_cat'
    )
    mouse_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='games_as_mouse',
        null=True,
        blank=True
    )
    cat1 = models.IntegerField(default=0, null=False)
    cat2 = models.IntegerField(default=2, null=False)
    cat3 = models.IntegerField(default=4, null=False)
    cat4 = models.IntegerField(default=6, null=False)
    mouse = models.IntegerField(default=59, null=False)
    cat_turn = models.BooleanField(default=True, null=False)
    status = models.IntegerField(default=GameStatus.CREATED, null=False)

    MIN_CELL = 0
    MAX_CELL = 63

    # Autor: Víctor Yrazusta Ibarra
    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)
        self.validate()

    # Autor: Alejandro Pascual Pozo
    def save(self, *args, **kwargs):
        self.validate()
        if self.status == GameStatus.CREATED and self.mouse_user is not None:
            self.status = GameStatus.ACTIVE
        super(Game, self).save(*args, **kwargs)

    # Autor: Víctor Yrazusta Ibarra
    def validate(self):
        if self.cat1 < Game.MIN_CELL or self.cat1 > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat2 < Game.MIN_CELL or self.cat2 > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat3 < Game.MIN_CELL or self.cat3 > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat4 < Game.MIN_CELL or self.cat4 > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.mouse < Game.MIN_CELL or self.mouse > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat1%2 != self.cat1//8%2:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat2%2 != self.cat2//8%2:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat3%2 != self.cat3//8%2:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.cat4%2 != self.cat4//8%2:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if self.mouse%2 != self.mouse//8%2:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
        if GameStatus(self.status) is None:
            raise ValidationError(constants.MSG_ERROR_GAMESTATUS)

    class Meta:
        app_label = 'datamodel'
     
    # Autor: Alejandro Pascual Pozo
    def __str__(self):
        message = (
            '(%d, %s)' % (self.id, GameStatus.to_string(self.status)) +
            '\tCat [%c] %s(%d, %d, %d, %d)' % (('X' if self.cat_turn else ' '), self.cat_user, self.cat1, self.cat2, self.cat3, self.cat4)
        )

        if self.mouse_user is not None:
            message += ' --- Mouse [%c] %s(%d)' % (('X' if not self.cat_turn else ' '), self.mouse_user, self.mouse)

        return message


class Move(models.Model):
    origin = models.IntegerField(null=False)
    target = models.IntegerField(null=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moves')
    date = models.DateField(null=False)

    # Autor: Víctor Yrazusta Ibarra
    def __init__(self, *args, **kwargs):
        super(Move, self).__init__(*args, **kwargs)
        self.date = datetime.now()

    # Autor: Alejandro Pascual Pozo
    def save(self, *args, **kwargs):
        self.validate()
        super(Move, self).save(*args, **kwargs)
    
    # Autor: Víctor Yrazusta Ibarra
    def validate(self):
        if self.origin < Game.MIN_CELL or self.origin > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target < Game.MIN_CELL or self.target > Game.MAX_CELL:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.origin%2 is not self.origin//8%2:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target%2 is not self.target//8%2:
            raise ValidationError(constants.MSG_ERROR_MOVE)

        if self.target == self.game.mouse:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target == self.game.cat1:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target == self.game.cat2:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target == self.game.cat3:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        if self.target == self.game.cat4:
            raise ValidationError(constants.MSG_ERROR_MOVE)

        if self.game.status != GameStatus.ACTIVE:
            raise ValidationError(constants.MSG_ERROR_MOVE)
    
        if self.game.cat_turn is True and self.game.cat_user == self.player:
            if not (self.origin%8 != 0 and self.target == self.origin+7):
                if not (self.origin%8 != 7 and self.target == self.origin+9):
                    raise ValidationError(constants.MSG_ERROR_MOVE)
                    
            if self.origin == self.game.cat1:
                self.game.cat1 = self.target
            elif self.origin == self.game.cat2:
                self.game.cat2 = self.target
            elif self.origin == self.game.cat3:
                self.game.cat3 = self.target
            elif self.origin == self.game.cat4:
                self.game.cat4 = self.target
            else:
                raise ValidationError(constants.MSG_ERROR_MOVE)
        elif self.game.cat_turn is False and self.game.mouse_user == self.player:
            if not (self.origin%8 != 0 and (self.target == self.origin+7 or self.target == self.origin-9)):
                if not (self.origin%8 != 7 and (self.target == self.origin+9 or self.target == self.origin-7)):
                    raise ValidationError(constants.MSG_ERROR_MOVE)

            if self.origin == self.game.mouse:
                self.game.mouse = self.target
            else:
                raise ValidationError(constants.MSG_ERROR_MOVE)
        else:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        
        self.game.cat_turn = not self.game.cat_turn
        self.game.save()

    class Meta:
        app_label = 'datamodel'


class CounterManager(models.Manager):

    # Autor: Alejandro Pascual Pozo
    def get_current_value(self):
        try:
            return self.get(pk=1).value
        except:
            return 0

    # Autor: Alejandro Pascual Pozo
    def inc(self):
        try:
            counter = self.get(pk=1)
        except:
            counter = Counter(pk=1)
        counter.value += 1
        super(Counter, counter).save()
        return counter.value


class Counter(models.Model):
    value = models.IntegerField(null=False, default=0)
    objects = CounterManager()

    # Autor: Víctor Yrazusta Ibarra
    def save(self, *args, **kwargs):
        raise ValidationError(constants.MSG_ERROR_NEW_COUNTER)

    # Autor: Alejandro Pascual Pozo
    def delete(self, *args, **kwargs):
        pass