from odoo import models, fields, exceptions, api, _
import logging
from odoo import api, models, _
from odoo.http import request
import secrets
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class AppApi(models.AbstractModel):
    _name = "my.app.api"
    _description = "APP API"

    @api.model
    def mobile_login(self, db, login, password):
        """
        Autentica al usuario y devuelve uid, username y session_id en JSON.
        Funciona en apps móviles sin depender de cookies.
        """
        try:
            # Autenticar sesión
            request.session.authenticate(db, login, password)

            if not request.session.uid:
                return {
                    "success": False,
                    "message": "Credenciales inválidas"
                }

            return {
                "success": True,
                "uid": request.session.uid,
                "username": request.env.user.login,
                "session_id": request.session.sid,
            }

        except Exception as e:
            _logger.exception("Error en mobile_login")
            return {
                "success": False,
                "message": str(e)
            }
    
    @api.model
    def get_partners(self, limit=5):
        """
        Ejemplo de endpoint que devuelve partners tras autenticación.
        """
        partners = (
            self.env["res.partner"]
            .sudo()
            .search_read(
                domain=[("is_company", "=", True)],
                fields=["id", "name", "email"],
                limit=limit,
            )
        )
        return partners

    @api.model
    def get_user_data(self, uid):
        """
        Obtiene los datos del usuario con el uid especificado.
        """
        user = self.env["res.users"].sudo().browse(uid)
        partner = user.partner_id
        partnerData = partner.read(fields=["vat", "name", "email", "mobile", "phone", "street", "city", "street2"])

        return partnerData

    @api.model
    def change_password(self, uid, old_password, new_password):
        # Verifica que el usuario exista
        user = self.env["res.users"].sudo().browse(uid)
        if not user.exists():
            raise exceptions.AccessError(_("Usuario no encontrado"))

        try:
            # Ejecuta como ese usuario para que Odoo valide la contraseña actual
            # y cambie la contraseña de forma segura.
            self.env["res.users"].with_user(uid).change_password(
                old_password, new_password
            )
        except exceptions.AccessDenied:
            # Contraseña actual incorrecta
            raise exceptions.AccessError(_("La contraseña actual es incorrecta"))
        except exceptions.UserError as e:
            # Cualquier otra validación de Odoo (políticas, etc.)
            raise exceptions.AccessError(
                e.name or _("No se pudo cambiar la contraseña")
            )

        _logger.info("Contraseña cambiada para el usuario %s (id=%s)", user.login, uid)
        return {"status": "success", "message": _("Contraseña cambiada correctamente")}

    @api.model
    def create_user_from_vat(self, vat, password):
        """
        Busca un partner por su cédula (vat).
        Si lo encuentra, crea un usuario asociado.
        El login será el mismo vat.
        """
        if not vat or not password:
            raise exceptions.UserError(
                _("Se requiere la cédula (vat) y la contraseña.")
            )

        # Buscar partner con el VAT
        partner = self.env["res.partner"].sudo().search([("vat", "=", vat)], limit=1)
        if not partner:
            raise exceptions.UserError(
                _("No se encontró ningún contacto con la cédula %s") % vat
            )

        # Verificar que no exista ya un usuario con ese login
        existing_user = (
            self.env["res.users"].sudo().search([("login", "=", vat)], limit=1)
        )
        if existing_user:
            raise exceptions.UserError(_("Ya existe un usuario con esta cédula."))

        # Crear el usuario
        new_user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": partner.name or vat,
                    "login": vat,
                    "password": password,
                    "partner_id": partner.id,
                }
            )
        )

        return {
            "status": "success",
            "message": _("Usuario creado correctamente."),
            "user_id": new_user.id,
            "login": new_user.login,
        }

    @api.model
    def request_registration(self, vat: str):
        # Buscar contacto
        partner = self.env["res.partner"].sudo().search([("vat", "=", vat)], limit=1)
        if not partner:
            return {
                "success": False,
                "error": f"No se encontró contacto con identificador {vat}",
            }

        # Verificar que no exista usuario
        user_exists = (
            self.env["res.users"]
            .sudo()
            .search([("partner_id", "=", partner.id)], limit=1)
        )
        if user_exists:
            return {
                "success": False,
                "error": f"Ya existe un usuario asociado al contacto {partner.name}",
            }

        if not partner.email:
            return {
                "success": False,
                "error": f"El contacto {partner.name} no tiene email",
            }
        

        signup_url = "localHost:8081"

        """


        # Crear usuario provisional con token (sin login aún)
        # Generar token seguro manualmente
        token = secrets.token_urlsafe(24)
        
        signup_user = self.env['res.users'].sudo().create({
            'name': partner.name,
            'login': partner.email,  # obligatorio
            'email': partner.email,
            'partner_id': partner.id,
            'signup_token': token,
            'signup_type': 'signup',
            'signup_valid': datetime.now() + timedelta(days=1)
        })

        # Construir link manual
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        signup_url = f"{base_url}/web/signup?token={token}"

        # Crear y enviar correo manualmente
        mail = self.env['mail.mail'].sudo().create({
            'subject': "Crear tu cuenta",
            'body_html': f"<p>Hola {partner.name},</p>"
                         f"<p>Haz clic en el siguiente link para crear tu cuenta y definir tu contraseña:</p>"
                         f"<p><a href='{signup_url}'>{signup_url}</a></p>",
            'email_to': partner.email,
        })
        mail.send()"""

        return {
            "success": True,
            "message": _("Correo de creación de cuenta generado para %s")
            % partner.email,
            "destinatary": partner.email,
            "signup_url": signup_url,
        }
