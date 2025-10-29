from odoo import models, fields, api

class Contact(models.Model):
    _inherit = "res.partner"

    company_name = fields.Char(string="Company Name")
    sector = fields.Text(string="Sector")
    country = fields.Char(string='Country')
    Team_Size = fields.Integer(string="Team Size")
    account_manager = fields.Many2one('res.users', string="Account Manager")

    # Leadership Chart
    leader_name = fields.Char(string="Leader Name")
    x_title = fields.Char(string="Title")

    # Department Head
    department_name = fields.Char(string="Department Name")
    department_title = fields.Char(string="Department Title")

    # Key Decision Makers
    decision_maker_name = fields.Char(string="Decision Maker Name")
    decision_maker_title = fields.Char(string="Decision Maker Title")

    # Industry, Segment & Market Position
    industry_id = fields.Many2one('res.partner.industry', string="Industry")
    segment = fields.Integer(string="Segment")
    Market_Share = fields.Integer(string="Market Share")
    Competitors = fields.Text(string="Competitors")
    Trends = fields.Text(string="Trends")
    Challenges = fields.Text(string="Challenges")

    # Departments and Divisions
    division_name = fields.Text(string='Division Name')
    manager = fields.Char(string='Manager')
    size = fields.Integer(string='Division Size')

    # Subdivisions / Regional Offices
    region_name = fields.Text(string='Region Name')
    region_manager = fields.Char(string='Region Manager')
    region_size = fields.Integer(string='Region Size')

    # ======================
    #   ONCHANGE METHODS
    # ======================

    @api.onchange('name')
    def _onchange_name_sync_company_name(self):
        """When user edits 'name', update 'company_name' immediately."""
        for rec in self:
            rec.company_name = rec.name

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """When user selects country, auto-fill 'country' text field."""
        for rec in self:
            rec.country = rec.country_id.name or ''

    @api.onchange('parent_id')
    def _onchange_parent_id_auto_fill(self):
        """
        When a parent company is selected, auto-fill key fields
        from that company's data.
        """
        for rec in self:
            if rec.parent_id and not rec.is_company:
                company = rec.parent_id
                rec.update({
                    'sector': company.sector,
                    'Team_Size': company.Team_Size,
                    'account_manager': company.account_manager.id,
                    'industry_id': company.industry_id.id,
                    'country': company.country,
                    'Market_Share': company.Market_Share,
                    'Competitors': company.Competitors,
                    'Trends': company.Trends,
                    'Challenges': company.Challenges,
                    'leader_name': company.leader_name,
                    'x_title': company.x_title,
                    'department_name': company.department_name,
                    'department_title': company.department_title,
                    'decision_maker_name': company.decision_maker_name,
                    'decision_maker_title': company.decision_maker_title,
                    'segment': company.segment,
                    'division_name': company.division_name,
                    'manager': company.manager,
                    'size': company.size,
                    'region_name': company.region_name,
                    'region_manager': company.region_manager,
                    'region_size': company.region_size,
                })

    # ======================
    #   CREATE / WRITE
    # ======================

    @api.model
    def create(self, vals):
        """Set defaults and copy from parent company if applicable."""
        # Sync name -> company_name
        if vals.get('name'):
            vals['company_name'] = vals['name']

        # Sync country_id -> country text
        if vals.get('country_id'):
            country = self.env['res.country'].browse(vals['country_id'])
            vals['country'] = country.name or ''

        # If creating a contact under a company
        parent_id = vals.get('parent_id')
        if parent_id:
            parent = self.env['res.partner'].browse(parent_id)
            if parent and not vals.get('is_company', False):
                vals.update({
                    'sector': parent.sector,
                    'Team_Size': parent.Team_Size,
                    'account_manager': parent.account_manager.id,
                    'industry_id': parent.industry_id.id,
                    'country': parent.country,
                    'Market_Share': parent.Market_Share,
                    'Competitors': parent.Competitors,
                    'Trends': parent.Trends,
                    'Challenges': parent.Challenges,
                    'leader_name': parent.leader_name,
                    'x_title': parent.x_title,
                    'department_name': parent.department_name,
                    'department_title': parent.department_title,
                    'decision_maker_name': parent.decision_maker_name,
                    'decision_maker_title': parent.decision_maker_title,
                    'segment': parent.segment,
                    'division_name': parent.division_name,
                    'manager': parent.manager,
                    'size': parent.size,
                    'region_name': parent.region_name,
                    'region_manager': parent.region_manager,
                    'region_size': parent.region_size,
                })

        return super(Contact, self).create(vals)

    def write(self, vals):
        """Keep name and country in sync when edited."""
        if 'name' in vals:
            vals['company_name'] = vals['name']

        if 'country_id' in vals:
            country_id = vals.get('country_id')
            if country_id:
                country = self.env['res.country'].browse(country_id)
                vals['country'] = country.name or ''
            else:
                vals['country'] = ''

        return super(Contact, self).write(vals)
