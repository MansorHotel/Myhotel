# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging
logging.basicConfig(level=logging.DEBUG)
from datetime import datetime


class HotelReservation(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'reservation_count' in counters:
            reservation_count = request.env['hotel.reservation'].search_count([])
            values['reservation_count'] = reservation_count
        return values

    # def _prepare_home_portal_values(self, counters):
    #     values = super()._prepare_home_portal_values(counters)
    #     if 'reservation_count' in counters:
    #         reservation_count = request.env['hotel.reservation'].search_count([])
    #         values['reservation_count'] = reservation_count
    #     return values

    @http.route('/my/home/reservation_list', type="http", auth='public', website=True)
    def get_reservation(self, **kw):
        # Get the selected state from the query parameters or use 'all' by default
        selected_state = request.params.get('state', 'all')
        reservation_details = request.env['hotel.reservation'].sudo().search([])
        vals = {
            'my_details': reservation_details,
            'page_name': 'reservation_details',
            'selected_state': selected_state,
        }
        return request.render('nthub_hotel_sys.reservation_details_page', vals)

    @http.route('/my/home/reservation_list/<string:state>', type="http", auth='public', website=True)
    def get_reservation_filtered(self, state=None, **kw):
        if state and state != 'all':
            domain = [('state', '=', state)]
            reservation_details = request.env['hotel.reservation'].sudo().search(domain)
        else:
            # Handle the case when 'all' is selected or no state is specified
            reservation_details = request.env['hotel.reservation'].sudo().search([])

        vals = {
            'my_details': reservation_details,
            'page_name': 'reservation_details',
            'selected_state': state,
        }
        return request.render('nthub_hotel_sys.reservation_details_page', vals)

    # @http.route('/my/home/reservation_list', type="http", auth='public', website=True)
    # def get_reservation(self, **kw):
    #     reservation_details = request.env['hotel.reservation'].sudo().search([])
    #
    #     vals = {
    #         'my_details': reservation_details,
    #         'page_name': 'reservation_details',
    #         'selected_state': 'all',  # Set the selected state to 'all' initially
    #     }
    #     return request.render('nthub_hotel_sys.reservation_details_page', vals)
    #
    # @http.route('/my/home/reservation_list/<string:state>', type="http", auth='public', website=True)
    # def get_reservation_filtered(self, state=None, **kw):
    #     if state and state != 'all':
    #         domain = [('state', '=', state)]
    #         reservation_details = request.env['hotel.reservation'].sudo().search(domain)
    #     else:
    #         # Handle the case when 'all' is selected or no state is specified
    #         reservation_details = request.env['hotel.reservation'].sudo().search([])
    #
    #     vals = {
    #         'my_details': reservation_details,
    #         'page_name': 'reservation_details',
    #         'selected_state': state,
    #     }
    #     return request.render('nthub_hotel_sys.reservation_details_page', vals)

    @http.route('/my/home/reservation/form', type="http", auth='public', website=True, csrf=True)
    def reservation_form_view(self, **kwargs):
        customer_ids = request.env['res.partner'].sudo().search([])
        room_ids = request.env['hotel.room'].sudo().search([])
        vals = {
            'customers': customer_ids,
            'rooms': room_ids,
            'page_name': 'reservation_form'
        }
        return request.render('nthub_hotel_sys.customer_reservation_form', vals)

    @http.route('/my/home/reservation/create', type="http", auth='public', website=True, csrf=True)
    def request_submit(self, **kwargs):
        # Extract form data from the request parameters
        customer_id = int(kwargs.get('customer_id'))
        room_id = int(kwargs.get('room_id'))
        res_start_date = kwargs.get('res_start_date')
        res_end_date = kwargs.get('res_end_date')

        try:
            # Validate the data (e.g., check for required fields)
            if not customer_id or not room_id or not res_start_date or not res_end_date:
                raise ValueError("Missing required data")

            # Convert start and end dates to datetime objects
            start_date = datetime.strptime(res_start_date, "%Y-%m-%d")
            end_date = datetime.strptime(res_end_date, "%Y-%m-%d")

            # Calculate the duration (difference between end date and start date)
            duration = (end_date - start_date).days + 1

            # Create a new reservation record in the database
            reservation_data = {
                'customer_id': customer_id,
                'room_id': room_id,
                'res_start_date': res_start_date,
                'res_end_date': res_end_date,
                'duration': duration,  # Assign the calculated duration
                # Add any other fields as needed
            }

            # Use the Odoo ORM to create a new reservation record
            reservation = request.env['hotel.reservation'].sudo().create(reservation_data)

            # Optionally, you can perform additional actions here, such as checking room availability

            # Redirect to a success page or return a success response
            return request.redirect('/my/home/reservation_list')

        except Exception as e:
            # Handle exceptions or validation errors here
            # Log the error for debugging purposes
            _logger.error(str(e))
            return request.render('nthub_hotel_sys.error_template', {'error_message': str(e)})

    @http.route(['/desired_reservation/<int:order_id>'], type="http", website=True, auth='public')
    def get_customer_form(self, order_id, **kw):
        order = request.env['hotel.reservation'].sudo().browse(order_id)
        vals = {
            "order": order,
            'page_name': 'desired_reservation'

        }
        return request.render('nthub_hotel_sys.customer_details_form_shown_link', vals)
