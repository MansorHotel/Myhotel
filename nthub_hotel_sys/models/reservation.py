# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import ValidationError
from collections import Counter

class ResPartner(models.Model):
    _inherit = 'res.partner'

    reservation_ids = fields.One2many('hotel.reservation', 'customer_id',readonly=True)





class Reservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Reservation'

    name = fields.Char(string='Reservation Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    customer_id = fields.Many2one('res.partner', string='Customer Name')
    phone = fields.Char(related="customer_id.phone")
    email = fields.Char(related="customer_id.email")
    address = fields.Char(related="customer_id.contact_address")

    id_type = fields.Selection([
        ('national_id', 'NID'),
        ('passport', 'Passport'),
        ('license_card', 'License Card'),
        ('resident_id', 'Resident ID'),
    ], string="ID Type")
    id_data = fields.Char(string='ID Data')

    res_start_date = fields.Date(string="Reservation Start Date")
    res_end_date = fields.Date(string="Reservation End Date")
    duration = fields.Integer(string="Duration")
    note = fields.Text(string='Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('ended', 'Ended'),
    ], string="status", default='draft')
    reservation_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ], required=True, string='Room Type')
    room_floor = fields.Integer(related="room_id.floor_num", string="Floor Number")
    room_unit_price = fields.Float(related="room_id.unit_price", string="Night Price")
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total", store=True)
    extras = fields.Many2many('hotel.extra')
    ex_price = fields.Float(string='Extras Price', compute='_compute_total_price', store=True)
    ex_sub_total = fields.Float(string="Extras Sub Total", compute="_compute_ex_sub_total", store=True)

    penalties = fields.Float(string='Penalties')
    final_price = fields.Float(string='Final Price', compute='_compute_final_price', store=True)
    today_date = fields.Date(string="Today's Date", default=fields.Date.context_today)
    reservation_id = fields.Many2one('account.move', string="Invoice")
    most = fields.Integer(compute='most_use')
    room_id = fields.Many2one('hotel.room', string="Room Number")

    @api.onchange('res_start_date', 'res_end_date', 'room_id', 'reservation_type')
    def _onchange_reservation_dates(self):
        # Calculate the domain to filter rooms that meet the conditions
        domain = self._get_available_rooms_domain()
        return {'domain': {'room_id': domain}}

    def _get_available_rooms_domain(self):
        if self.res_start_date and not self.res_end_date and not self.reservation_type:
            return self._get_rooms_with_no_reservations()
        elif self.res_start_date and self.reservation_type and not self.res_end_date:
            return self._get_rooms_with_matching_type()
        elif self.res_start_date and self.res_end_date and not self.reservation_type:
            return self._get_all_rooms_with_period()
        elif self.res_start_date and self.res_end_date and self.reservation_type:
            return self._get_rooms_matching_with_period()

    def _get_rooms_with_no_reservations(self):
        # Get all rooms
        all_rooms = self.env['hotel.room'].search([])

        # Initialize a list to store room IDs that have no reservations
        rooms_matching_conditions = []

        for room in all_rooms:
            # Check if the room is currently maintained and skip it
            if room.state == 'maintained':
                continue

            # Check if there are any 'scheduled' or 'running' reservations for the room
            conflicting_reservations = self.env['hotel.reservation'].search([
                ('room_id', '=', room.id),
                ('state', 'in', ['scheduled', 'running'])
            ])

            # If there are no conflicting reservations, add the room to the list
            if not conflicting_reservations:
                rooms_matching_conditions.append(room.id)

        # Calculate the domain by including rooms that meet the conditions
        return [('id', 'in', rooms_matching_conditions)]

    def _get_rooms_with_matching_type(self):
        # Find rooms with matching reservation_type and no reservations
        matching_rooms = self.env['hotel.room'].search([('room_type', '=', self.reservation_type)])
        rooms_matching_conditions = []

        for room in matching_rooms:
            # Check if the room is currently maintained and skip it
            if room.state == 'maintained':
                continue

            # If the room has no reservations, add it to the list
            if not room.reservation_ids:
                rooms_matching_conditions.append(room.id)

        # Calculate the domain by including rooms that meet the conditions
        return [('id', 'in', rooms_matching_conditions)]

    def _get_all_rooms_with_period(self):
        # Check if res_start_date and res_end_date are provided
        if self.res_start_date and self.res_end_date:
            # Create a list of days for the reservation period
            reservation_days = [self.res_start_date + timedelta(days=x) for x in
                                range((self.res_end_date - self.res_start_date).days + 1)]

            # Get all rooms that are not in 'maintained' state
            all_rooms = self.env['hotel.room'].search([('state', '!=', 'maintained')])

            # Initialize a list to store room IDs that meet the conditions
            rooms_matching_conditions = []

            for room in all_rooms:
                # Check if the room is currently maintained and skip it
                if room.state == 'maintained':
                    continue

                # Create a list of days for each room's existing reservations
                room_reservation_days = []
                for reservation in room.reservation_ids:
                    # Check if reservation is not in 'ended' state
                    if reservation.state == 'ended' or reservation.state == 'draft':
                        continue

                    # Create a list of days for the current reservation
                    current_reservation_days = [reservation.res_start_date + timedelta(days=x) for x in
                                                range((reservation.res_end_date - reservation.res_start_date).days + 1)]

                    # Check if there are any overlapping days between the current reservation and the new reservation
                    if any(day in current_reservation_days for day in reservation_days):
                        break  # Room has a conflicting reservation, so we break out of the loop
                else:
                    # This part of the code is reached if there were no conflicting reservations for the room
                    rooms_matching_conditions.append(room.id)

            # Calculate the domain by including rooms that meet the conditions
            return [('id', 'in', rooms_matching_conditions)]
        else:
            # If res_start_date and res_end_date are not provided, return an empty domain
            return []

    def _get_rooms_matching_with_period(self):
        # Create a list of days for the reservation period
        reservation_days = [self.res_start_date + timedelta(days=x) for x in
                            range((self.res_end_date - self.res_start_date).days + 1)] if self.res_end_date else []

        # Get all rooms that match the reservation type
        matching_rooms = self.env['hotel.room'].search([('room_type', '=', self.reservation_type)])

        # Initialize a list to store room IDs that meet the conditions
        rooms_matching_conditions = []

        for room in matching_rooms:
            # Check if the room is currently maintained and skip it
            if room.state == 'maintained':
                continue

            # Create a list of days for each room's existing reservations
            room_reservation_days = []
            for reservation in room.reservation_ids:
                # Check if reservation is not in 'ended' state
                if reservation.state == 'ended' or reservation.state == 'draft':
                    continue

                # Create a list of days for the current reservation
                current_reservation_days = [reservation.res_start_date + timedelta(days=x) for x in
                                            range((reservation.res_end_date - reservation.res_start_date).days + 1)]

                # Check if there are any overlapping days between the current reservation and the new reservation
                if any(day in current_reservation_days for day in reservation_days):
                    break  # Room has a conflicting reservation, so we break out of the loop

            else:
                # This part of the code is reached if there were no conflicting reservations for the room
                rooms_matching_conditions.append(room.id)

        # Calculate the domain by including rooms that meet the conditions
        return [('id', 'in', rooms_matching_conditions)]



    @api.depends('room_id')
    def most_use(self):
        lst = []
        self.most = False
        if self.search([]):
            for rec in self.search([]):
                lst.append(rec.room_id.id)
            counted_items = Counter(lst)
            most_common_item, count = counted_items.most_common(1)[0]
            for res in self.search([]):
                res.most = most_common_item

    def unlink(self):
        rooms_to_empty = self.mapped('room_id')
        delet = super(Reservation, self).unlink()

        # Check if there are any other active reservations for the rooms
        if delet:
            for room in rooms_to_empty:
                active_reservations = self.env['hotel.reservation'].search(
                    [('room_id', '=', room.id), ('state', '=', 'running')])
                if not active_reservations:
                    room.write({'state': 'empty'})

        return True

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or _('New')
        res = super(Reservation, self).create(vals)
        return res

    @api.onchange('res_start_date', 'res_end_date')
    def onchange_dates(self):
        if self.res_start_date and self.res_end_date:
            delta = self.res_end_date - self.res_start_date
            self.duration = delta.days + 1
        else:
            self.duration = 0

    @api.onchange('res_start_date', 'duration')
    def onchange_duration(self):
        if self.duration and self.res_start_date:
            self.res_end_date = self.res_start_date + timedelta(days=self.duration - 1)
        else:
            self.res_end_date = False

    @api.depends('extras')
    def _compute_total_price(self):
        for order in self:
            total = sum(extra.price for extra in order.extras)
            order.ex_price = total

    @api.depends('room_unit_price', 'ex_price', 'duration', 'penalties')
    def _compute_final_price(self):
        for reservation in self:
            final_price = 0.0

            if reservation.room_unit_price:
                final_price += reservation.room_unit_price

            if reservation.ex_price:
                final_price += reservation.ex_price

            if reservation.duration:
                final_price *= reservation.duration

            if reservation.penalties:
                final_price += reservation.penalties

            reservation.final_price = final_price

    def action_confirm(self):
        for rec in self:
            if datetime.now().date() < rec.res_start_date:
                rec.state = 'scheduled'
            elif rec.res_start_date == datetime.now().date():
                rec.state = 'running'
                rec.room_id.state = 'busy'

    def check_reservation_status(self):
        self.onchange_state_running()
        self.onchange_state_ended()

    def onchange_state_ended(self):
        for rec in self.search([('state', '=', 'running')]):
            if rec.res_end_date == datetime.now().date():
                rec.state = 'ended'
                rec.room_id.state = 'empty'
                rec.room_id.reservation_ids -= rec

    def onchange_state_running(self):
        for rec in self.search([('state', '=', 'scheduled')]):
            if rec.res_start_date == datetime.now().date():
                rec.state = 'running'
                rec.room_id.state = 'busy'

    @api.depends('room_unit_price', 'duration')
    def _compute_sub_total(self):
        for reservation in self:
            sub_total = 0.0
            if reservation.room_unit_price and reservation.duration:
                sub_total = reservation.room_unit_price * reservation.duration
            reservation.sub_total = sub_total

    @api.depends('ex_price', 'duration')
    def _compute_ex_sub_total(self):
        for reservation in self:
            ex_sub_total = 0.0
            if reservation.ex_price and reservation.duration:
                ex_sub_total = reservation.ex_price * reservation.duration
            reservation.ex_sub_total = ex_sub_total

    def create_customer_invoice(self):
        for reservation in self:
            if reservation.state != 'running':
                raise ValueError(_('Cannot create an invoice for a reservation that is not in the running state.'))

            if reservation.res_end_date > datetime.now().date():
                reservation.res_end_date = datetime.now().date()
                reservation.onchange_dates()

            invoice_line_vals = {
                'name': reservation.name,
                'quantity': reservation.duration,
                'price_unit': reservation.room_unit_price,
            }

            invoice_line_ids = [(0, 0, invoice_line_vals)]

            if reservation.ex_price:
                # If ex_price exists, add it as a separate line in the invoice
                ex_price_line = {
                    'name': _('Extra Charges'),
                    'quantity': reservation.duration,
                    'price_unit': reservation.ex_price,
                }
                invoice_line_ids.append((0, 0, ex_price_line))

            if reservation.penalties:
                # If penalties exist, add them as a separate line in the invoice
                penalties_line = {
                    'name': _('Penalties'),
                    'quantity': 1,
                    'price_unit': reservation.penalties,
                }
                invoice_line_ids.append((0, 0, penalties_line))

            invoice_vals = {
                'name': reservation.name,
                'partner_id': reservation.customer_id.id,
                'invoice_date': datetime.now().date(),
                'move_type': 'out_invoice',
                'invoice_line_ids': invoice_line_ids,
            }

            invoice = self.env['account.move'].create(invoice_vals)
            self.reservation_id = invoice.id

            if reservation.room_id:
                reservation.room_id.state = 'empty'
            reservation.state = 'ended'

    def return_to_active_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Installments Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.reservation_id.id,
            'target': 'current',
        }

    @api.constrains('customer_id', 'room_id', 'res_start_date', 'res_end_date', 'duration')
    def _check_fields_not_empty(self):
        for record in self:
            if not record.customer_id or not record.room_id or not record.res_start_date or not record.res_end_date:
                raise ValidationError("Please fill all required fields."
                                      "customer,room,2 dates,duration")

    @api.constrains('res_start_date')
    def _check_start_date(self):
        for record in self:
            if record.res_start_date < datetime.now().date():
                raise ValidationError("The reservation start date cannot be reserved")





