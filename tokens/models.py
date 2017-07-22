import json
import os
import subprocess

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .conf import PHASES, TOKEN_TYPES
from .utils import generate_migration, generate_contracts
from . import web3


class Token(models.Model):
    public_name = models.CharField(max_length=200)

    symbol = models.CharField(max_length=4)

    decimals = models.IntegerField(
        default=18,
        validators=[MaxValueValidator(20), MinValueValidator(0)]
    )

    cap = models.IntegerField(
        blank=True, null=True
    )

    token_type = models.CharField(
        max_length=20,
        choices=TOKEN_TYPES,
        blank=True
    )

    start_block_offset = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )

    end_block_offset = models.IntegerField(
        default=300,
        validators=[MinValueValidator(300)]
    )

    rate = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0)]
    )

    ico_start_date = models.DateTimeField()
    ico_end_date = models.DateTimeField()

    @property
    def class_name(self):
        return ''.join(
            map(lambda s: s.title(), self.public_name.split())
        )

    @property
    def crowdsale_class_name(self):
        return self.class_name + self.token_type + 'Crowdsale'

    @property
    def meta(self):
        meta_json_path = os.path.join(
            settings.SOLIDITY_ABI_DIR,
            '{}.json'.format(self.crowdsale_class_name)
        )

        if not os.path.exists(meta_json_path):
            return {}
        else:
            with open(meta_json_path) as f:
                return json.load(f)

    @property
    def abi(self):
        return self.meta.get('abi')

    @property
    def contract_address(self):
        if not self.pk:
            return None

        networks = self.meta.get('networks', {}).values()
        return sorted(networks, key=lambda n: n['updated_at'])[-1]['address']


    @property
    def _cap_reached(self):
        if self.token_type == 'Uncapped':
            return False

        contract = web3.eth.contract(address=self.contract_address, abi=self.abi)
        return contract.call().hasEnded()

    @property
    def phase(self):
        if not self.pk:
            return None

        now = timezone.now()

        if now < self.ico_start_date:
            return 'UPCOMING'
        elif now < self.ico_end_date and not self._cap_reached:
            return 'ACTIVE'
        elif self._cap_reached or not self.cap:
            return 'COMPLETED'
        else:
            return 'FAILED'

    def clean(self):
        now = timezone.now()

        if not self.ico_start_date:
            self.ico_start_date = now

        if self.cap:
            self.token_type = TOKEN_TYPES[0][1]
        else:
            self.token_type = TOKEN_TYPES[1][1]

    def save(self, *args, **kwargs):
        self.clean()

        generate_contracts(self)
        generate_migration(self)

        self.compile()
        self.deploy()

        super().save(*args, **kwargs)

    def compile(self):
        return subprocess.check_output(
            ['npm', 'run', 'compile'],
            cwd=os.path.join(settings.BASE_DIR, 'core')
        )

    def deploy(self):
        return subprocess.check_output(
            ['npm', 'run', 'deploy'],
            cwd=os.path.join(settings.BASE_DIR, 'core')
        )
