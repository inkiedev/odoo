from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)


class AppApi(models.AbstractModel):
    _name = "my.app.api"
    _description = "APP API"
    
    @api.model
    def get_user_data(self, uid):
        """
        Obtiene los datos del usuario con el uid especificado.
        """
        user = self.env['res.users'].sudo().browse(uid)
        if not user.exists():
            return {'error': 'Usuario no encontrado'}
        
        partner = user.partner_id
        
        user_data = {
            'id': user.id,
            'login': user.login,
            'name': user.name,
            'email': user.email,
            'active': user.active,
            'partner_id': partner.id,
            'partner_name': partner.name,
            'partner_email': partner.email,
            'partner_vat': partner.vat
        }
        
        return user_data
