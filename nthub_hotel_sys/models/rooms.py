# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Hotel(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel'

    name = fields.Char(string="Room Number")
    reference = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                            default=lambda self: _('New'))
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ], required=True, default='single', string='Room Type')
    floor_num = fields.Integer(string="Floor Number")
    state = fields.Selection([
        ('empty', 'Empty'),
        ('busy', 'Busy'),
        ('maintained', 'Maintained'),
    ], string='status', default='empty')

    unit_price = fields.Float(string="Night Price")
    reservation_ids = fields.One2many('hotel.reservation', 'room_id', string='Reservations')


    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('hotel.room') or _('New')
        res = super(Hotel, self).create(vals)
        return res

    @api.constrains('name')
    def check_name(self):
        for rec in self:
            rooms = self.env['hotel.room'].search([('name', '=', rec.name), ('id', '!=', rec.id)])
            if rooms:
                raise ValidationError(_("Name %s Already Exists" % rec.name))

    def action_maintain(self):
        for rec in self:
            rec.state = 'maintained'

    def action_empty(self):
        for rec in self:
            rec.state = 'empty'

