# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class Extra(models.Model):
    _name = 'hotel.extra'
    _description = 'Extra Utilities'

    name = fields.Char(string='Name', required=True, tracking=True)
    price = fields.Float()
    note = fields.Text(string='Description')

