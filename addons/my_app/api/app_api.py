from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)


class AppApi(models.AbstractModel):
    _name = "my.app.api"
    _description = "APP API"

    @api.model
    def authenticate(self, db, username, password):
        """
        Servicio de autenticación para la app.
        Similar a common.authenticate pero expuesto desde un modelo.
        """
        # Usamos el registro de usuarios de Odoo
        uid = self.env['res.users'].sudo().authenticate(db, username, password, {})
        if not uid:
            logger.warning("❌ Falló autenticación para usuario %s", username)
            return {
                "success": False,
                "message": _("Credenciales inválidas"),
            }

        logger.info("✅ Usuario %s autenticado con UID %s", username, uid)
        return {
            "success": True,
            "uid": uid,
            "username": username,
        }

    @api.model
    def get_partners(self, limit=5):
        """
        Ejemplo de endpoint que devuelve partners tras autenticación.
        """
        partners = self.env['res.partner'].sudo().search_read(
            domain=[('is_company', '=', True)],
            fields=['id', 'name', 'email'],
            limit=limit
        )
        return partners
    
    def get_user_info(self, uid):
        """
        Ejemplo de endpoint que devuelve información del usuario tras autenticación.
        """
        user = self.env['res.users'].sudo().browse(uid)
        partner = user.partner_id
        partnerData = partner.read(
            fields=['name', 'email', 'vat']
        )

        return partnerData
