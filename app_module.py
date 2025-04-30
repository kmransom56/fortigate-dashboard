"""
Flask App Module for FortiSwitch IP Management

This module provides a Flask web interface for managing FortiSwitch IP addresses.
It can be integrated into your existing FortiGate dashboard application.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
import logging
from fortiswitch_manager import FortiSwitchManager

# Set up logging
logger = logging.getLogger(__name__)

# Create a Blueprint for the FortiSwitch management functionality
fortiswitch_bp = Blueprint('fortiswitch', __name__, url_prefix='/fortiswitch')


@fortiswitch_bp.route('/', methods=['GET'])
def index():
    """
    Display the FortiSwitch management dashboard.
    """
    try:
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Get list of managed switches
        result = manager.get_managed_switches()
        
        if 'results' in result:
            switches = result['results']
            return render_template('fortiswitch/index.html', switches=switches)
        else:
            flash('Error retrieving FortiSwitch data', 'error')
            logger.error(f"Error retrieving FortiSwitch data: {result.get('error', 'Unknown error')}")
            return render_template('fortiswitch/index.html', switches=[])
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        logger.exception("Exception in FortiSwitch index route")
        return render_template('fortiswitch/index.html', switches=[])


@fortiswitch_bp.route('/details/<switch_id>', methods=['GET'])
def switch_details(switch_id):
    """
    Display details for a specific FortiSwitch.
    """
    try:
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Get switch details
        switch_result = manager.get_switch_details(switch_id)
        
        # Get connected devices
        devices_result = manager.get_connected_devices(switch_id)
        
        # Get port information
        ports_result = manager.get_switch_ports(switch_id)
        
        switch = switch_result.get('results', {})
        devices = devices_result.get('results', [])
        ports = ports_result.get('results', [])
        
        return render_template(
            'fortiswitch/details.html',
            switch=switch,
            devices=devices,
            ports=ports,
            switch_id=switch_id
        )
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        logger.exception(f"Exception in FortiSwitch details route for switch {switch_id}")
        return redirect(url_for('fortiswitch.index'))


@fortiswitch_bp.route('/ip_form/<switch_id>', methods=['GET'])
def ip_change_form(switch_id):
    """
    Display form for changing a FortiSwitch IP address.
    """
    try:
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Get switch details to show current IP
        result = manager.get_switch_details(switch_id)
        
        if 'results' in result:
            switch = result['results']
            current_ip = switch.get('fsw-wan1-ip', '')
            current_netmask = switch.get('fsw-wan1-netmask', '255.255.255.0')
            
            return render_template(
                'fortiswitch/ip_form.html',
                switch_id=switch_id,
                switch_name=switch.get('name', switch_id),
                current_ip=current_ip,
                current_netmask=current_netmask
            )
        else:
            flash('Error retrieving FortiSwitch data', 'error')
            logger.error(f"Error retrieving FortiSwitch data: {result.get('error', 'Unknown error')}")
            return redirect(url_for('fortiswitch.index'))
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        logger.exception(f"Exception in FortiSwitch IP form route for switch {switch_id}")
        return redirect(url_for('fortiswitch.index'))


@fortiswitch_bp.route('/change_ip/<switch_id>', methods=['POST'])
def change_ip(switch_id):
    """
    Handle form submission for changing a FortiSwitch IP address.
    """
    try:
        # Get form data
        new_ip = request.form.get('new_ip', '')
        new_netmask = request.form.get('new_netmask', '255.255.255.0')
        
        if not new_ip:
            flash('IP address is required', 'error')
            return redirect(url_for('fortiswitch.ip_change_form', switch_id=switch_id))
        
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Change the IP address
        result = manager.change_switch_ip(switch_id, new_ip, new_netmask)
        
        if result.get('success', False):
            flash(f'Successfully changed IP address to {new_ip}', 'success')
            logger.info(f"Successfully changed IP for switch {switch_id} to {new_ip}")
            return redirect(url_for('fortiswitch.details', switch_id=switch_id))
        else:
            flash(f'Error changing IP address: {result.get("message", "Unknown error")}', 'error')
            logger.error(f"Error changing IP for switch {switch_id}: {result.get('message', 'Unknown error')}")
            return redirect(url_for('fortiswitch.ip_change_form', switch_id=switch_id))
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        logger.exception(f"Exception in FortiSwitch change IP route for switch {switch_id}")
        return redirect(url_for('fortiswitch.ip_change_form', switch_id=switch_id))


@fortiswitch_bp.route('/api/switches', methods=['GET'])
def api_get_switches():
    """
    API endpoint to get all managed FortiSwitches.
    """
    try:
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Get list of managed switches
        result = manager.get_managed_switches()
        
        return jsonify(result)
    
    except Exception as e:
        logger.exception("Exception in FortiSwitch API get switches")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@fortiswitch_bp.route('/api/switch/<switch_id>', methods=['GET'])
def api_get_switch(switch_id):
    """
    API endpoint to get details for a specific FortiSwitch.
    """
    try:
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Get switch details
        result = manager.get_switch_details(switch_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.exception(f"Exception in FortiSwitch API get switch details for {switch_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@fortiswitch_bp.route('/api/switch/<switch_id>/ip', methods=['PUT'])
def api_change_ip(switch_id):
    """
    API endpoint to change a FortiSwitch IP address.
    """
    try:
        # Get JSON data
        data = request.json
        new_ip = data.get('new_ip', '')
        new_netmask = data.get('new_netmask', '255.255.255.0')
        
        if not new_ip:
            return jsonify({
                'success': False,
                'error': 'IP address is required'
            }), 400
        
        # Get FortiGate credentials from app config
        fortigate_ip = current_app.config.get('FORTIGATE_IP')
        api_token = current_app.config.get('FORTIGATE_API_TOKEN')
        
        # Create FortiSwitch manager
        manager = FortiSwitchManager(fortigate_ip, api_token)
        
        # Change the IP address
        result = manager.change_switch_ip(switch_id, new_ip, new_netmask)
        
        if result.get('success', False):
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.exception(f"Exception in FortiSwitch API change IP for {switch_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_blueprint(app):
    """
    Register the FortiSwitch blueprint with the Flask application.
    """
    app.register_blueprint(fortiswitch_bp)
    logger.info("Registered FortiSwitch blueprint")