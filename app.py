#!/usr/bin/env python3
"""
TMS Dashboard - Python Flask Web Server
Simple, lightweight dashboard that can be accessed from any browser
"""

from flask import Flask, render_template, jsonify, request, session, redirect
from flask_cors import CORS
from flask_session import Session
import json
import os
import requests
import time
from datetime import datetime, timedelta
from src.auth import authenticate_user, is_valid_username, get_all_users
from src.session import create_session
from src.audit import audit_action, log_user_action, get_client_ip
from src.audit_db import initialize_database, log_action, get_audit_trail, get_user_actions, get_customer_actions, get_audit_stats
from src.jobs import (initialize_jobs_database, create_job, update_job, get_user_jobs, 
                      get_job_customers, get_job_details, get_cached_appstatus,
                      cache_appstatus, cleanup_expired_cache, get_cached_appstatus_batch,
                      invalidate_appstatus_cache, get_cache_stats)
from src.prod_customer_data import (initialize_prod_customer_data_db, save_prod_customer_data,
                                     get_prod_customer_data, get_all_prod_customer_data,
                                     delete_prod_customer_data, generate_and_save_batches,
                                     get_batches_for_cluster_device, delete_batch,
                                     delete_all_batches_for_cluster_device, assign_batch_to_user,
                                     assign_batches_bulk)

app = Flask(__name__)
CORS(app)

# Session timeout configuration (in minutes)
SESSION_TIMEOUT_MINUTES = 15

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_TIMEOUT_MINUTES * 60  # Convert to seconds
app.config['SESSION_COOKIE_SECURE'] = False  # For localhost development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_USE_SIGNER'] = True
app.secret_key = 'tms-dashboard-secret-key-2024'
Session(app)

# Initialize databases
initialize_database()
initialize_jobs_database()
initialize_prod_customer_data_db()

# ============================================================================
# SESSION TIMEOUT MIDDLEWARE
# ============================================================================
@app.before_request
def check_session_timeout():
    """
    Check if user session has expired based on last activity.
    If expired, clear the session and redirect to login.
    """
    # Exclude login/logout routes from timeout check
    if request.endpoint in ['login', 'api_login', 'logout', 'api_logout']:
        return
    
    # Only check timeout for authenticated users
    if 'user_id' in session:
        last_activity = session.get('last_activity')
        
        if last_activity:
            try:
                # Parse the ISO format timestamp
                last_activity_time = datetime.fromisoformat(last_activity)
                current_time = datetime.now()
                
                # Calculate elapsed time
                elapsed = current_time - last_activity_time
                timeout_duration = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
                
                # Check if session has expired
                if elapsed > timeout_duration:
                    # Session expired - clear it
                    session.clear()
                    
                    # For API requests, return 401
                    if request.path.startswith('/api/'):
                        return jsonify({'error': 'Session expired', 'expired': True}), 401
                    # For page requests, redirect to login
                    else:
                        return redirect('/login')
            except (ValueError, TypeError) as e:
                # If timestamp parsing fails, log it but don't block the request
                print(f'[SESSION] Error parsing timestamp: {e}')
        
        # Update last activity timestamp on every request
        session['last_activity'] = datetime.now().isoformat()
        session.modified = True

# ============================================================================

# Decorator for authentication
def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Redirect browsers to login page for GET requests
            if request.method == 'GET':
                return redirect('/login')
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)

    return decorated_function

# ============================================================================
# ROLE-BASED ACCESS CONTROL HELPERS
# ============================================================================

ADMIN_USERS = {'prasad', 'admin'}

def is_admin_user():
    """Check if current user is an admin user"""
    user_id = session.get('user_id', '').lower()
    return user_id in ADMIN_USERS

def get_current_user():
    """Get current user ID from session"""
    return session.get('user_id', 'unknown')

def require_admin(f):
    """Decorator to require admin privileges"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.method == 'GET':
                return redirect('/login')
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not is_admin_user():
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)

    return decorated_function

# In-memory storage for demo data
demo_data = {
    "685102e6fc1511ef9ee8561b853a244c": {"action_code": 5, "action_desc": "pe-direct"},
    "6866cf36c19511f0a69e0a3464f46ecd": {"action_code": 2, "action_desc": "pe-enable"},
    "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d": {"action_code": 3, "action_desc": "t-enable"},
    "8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e": {"action_code": 4, "action_desc": "pe-finalize"},
    "9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f": {"action_code": 1, "action_desc": "tran-begin"},
}

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login')
def login():
    """Serve the login page"""
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate username exists
        if not is_valid_username(username):
            return jsonify({'success': False, 'message': 'Invalid username'}), 401
        
        # Authenticate user
        if not authenticate_user(username, password):
            return jsonify({'success': False, 'message': 'Invalid password'}), 401
        
        # Create session
        session_data = create_session(username)
        session.update(session_data)
        
        # Log the login action
        log_user_action(
            user_id=username,
            action_type='Login',
            ip_address=get_client_ip(request),
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': username
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/logout')
def logout():
    """Logout endpoint"""
    user_id = session.get('user_id', 'unknown')
    session.clear()
    
    # Log the logout action
    log_user_action(
        user_id=user_id,
        action_type='Logout',
        ip_address=get_client_ip(request),
        status='success'
    )
    
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout API endpoint"""
    user_id = session.get('user_id', 'unknown')
    session.clear()
    
    # Log the logout action
    log_user_action(
        user_id=user_id,
        action_type='Logout',
        ip_address=get_client_ip(request),
        status='success'
    )
    
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/user/info')
@require_auth
def user_info():
    """Get current user info"""
    return jsonify({
        'user_id': session.get('user_id'),
        'login_time': session.get('login_time'),
        'last_activity': session.get('last_activity')
    }), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get list of valid usernames (for demo purposes)"""
    return jsonify({'users': get_all_users()}), 200

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/')
@require_auth
def index():
    """Serve the main dashboard page"""
    response = render_template('index.html')
    # Disable caching for development
    from flask import make_response
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api/transition/state', methods=['GET', 'POST'])
@require_auth
@audit_action('Trans-Begin')
def get_transition_state():
    """API endpoint to get transition state data"""
    return jsonify(demo_data)


def get_action_code(action_name):
    """
    Map action name (from frontend) to action code (for jobs.db).
    Case-insensitive matching to handle various formatting from frontend.
    
    Args:
        action_name (str): Action name from frontend (e.g., 'Trans-Begin', 'PE-Enable')
    
    Returns:
        int: Action code (1-6), or None if not recognized
    """
    # Normalize to lowercase for matching
    normalized = action_name.lower() if action_name else None
    
    action_mapping = {
        'tran-begin': 1,
        'Tran-Begin': 1,
        'trans-begin': 1,
        'pe-enable': 2,
        't-enable': 3,
        'pe-finalize': 4,
        'pe-direct': 5,
    }
    
    result = action_mapping.get(normalized)
    if result:
        return result
    
    # If not found, log warning about unrecognized action
    if action_name:
        print(f"[SET_ACTION] WARNING: Unrecognized action name='{action_name}' (normalized='{normalized}')")
    
    return None


@app.route('/proxy_fetch', methods=['POST'])
@require_auth
def proxy_fetch():
    """Proxy endpoint to fetch or post data to external API with job tracking"""
    # Initialize job_id as None for tracking
    job_id = None
    action_type = None
    customer_ids = None
    user_id = session.get('user_id', 'unknown')
    
    try:
        data = request.get_json()
        url = data.get('url')
        token = data.get('token', '')
        is_post = data.get('isPost', False)
        post_data = data.get('postData', None)
        content_type = data.get('contentType', 'application/json')
        
        # Extract action and customer IDs for Set Action requests
        if post_data and isinstance(post_data, dict):
            action_type = post_data.get('action')
            customer_ids = post_data.get('cids')
        
        # Log the start of the request
        if action_type and customer_ids:
            print(f"[SET_ACTION] Starting: user={user_id}, action={action_type}, cid_count={len(customer_ids)}")
            
            # CREATE JOB with IN_PROGRESS status first
            action_code = get_action_code(action_type)
            if action_code:
                print(f"[SET_ACTION] Creating job: action_code={action_code}, action_name={action_type}, cid_count={len(customer_ids)}")
                job = create_job(
                    user_id=user_id,
                    action_code=action_code,
                    action_name=action_type,
                    cids=customer_ids,
                    cluster_url=url,
                    request_payload=post_data,
                    response_summary="In progress...",
                    status='IN_PROGRESS'
                )
                
                if job:
                    job_id = job['job_id']
                    print(f"[SET_ACTION] Job created with job_id={job_id}, status=IN_PROGRESS")
                else:
                    print(f"[SET_ACTION] WARNING: Failed to create job")
        
        headers = {'Content-Type': content_type}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if is_post and post_data:
            # Handle different content types
            if content_type == 'application/x-www-form-urlencoded':
                response = requests.post(url, headers=headers, data=post_data, timeout=35)
            else:
                response = requests.post(url, headers=headers, json=post_data, timeout=35)
        else:
            response = requests.get(url, headers=headers, timeout=35)
        
        # Prepare response and log action
        response_data = None
        if response.status_code in [200, 201]:
            try:
                json_data = response.json()
                response_data = jsonify({
                    'status': 'success',
                    'data': json_data,
                    'httpStatus': response.status_code
                })
                
                # Log the action and UPDATE JOB if we have action_type and customer_ids
                if action_type and customer_ids:
                    api_success = json_data.get('success', True) if isinstance(json_data, dict) else True
                    status = 'SUCCESS' if api_success else 'FAILED'
                    error_msg = json_data.get('message') if isinstance(json_data, dict) and not api_success else None
                    response_summary = json.dumps(json_data) if isinstance(json_data, dict) else str(json_data)
                    
                    # Log to audit log
                    print(f"[SET_ACTION] Logging audit: action={action_type}, customer_ids={customer_ids}")
                    log_user_action(
                        user_id=user_id,
                        action_type=action_type,
                        customer_ids=customer_ids,
                        ip_address=get_client_ip(request),
                        status='success' if api_success else 'failure',
                        error_message=error_msg
                    )
                    
                    # UPDATE JOB with result status
                    if job_id:
                        update_job(
                            job_id=job_id,
                            status=status,
                            http_status=response.status_code,
                            error_message=error_msg if not api_success else None,
                            response_summary=response_summary
                        )
                        print(f"[SET_ACTION] Job {job_id} updated: status={status}, http_status={response.status_code}")
                        # Add job_id to response so frontend can display it
                        response_json = response_data.get_json()
                        response_json['job_id'] = job_id
                        response_data = jsonify(response_json)
                    else:
                        print(f"[SET_ACTION] WARNING: Job creation failed earlier, cannot update with result")
                
                return response_data
            except ValueError as e:
                print(f"[PROXY] JSON parse error: {str(e)}")
                # Update job to FAILED if it was created
                if job_id:
                    update_job(job_id=job_id, status='FAILED', http_status=500, 
                              error_message=f'JSON parse error: {str(e)}')
                print("="*60 + "\n")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid JSON response: {str(e)}',
                    'httpStatus': response.status_code
                }), 500
        else:
            error_msg = f'API returned status {response.status_code}: {response.text[:200]}'
            
            # Log failed action
            if action_type and customer_ids:
                print(f"[SET_ACTION] FAILED: HTTP {response.status_code}, {error_msg}")
                log_user_action(
                    user_id=user_id,
                    action_type=action_type,
                    customer_ids=customer_ids,
                    ip_address=get_client_ip(request),
                    status='failure',
                    error_message=error_msg
                )
                
                # UPDATE job to FAILED
                if job_id:
                    update_job(job_id=job_id, status='FAILED', http_status=response.status_code,
                              error_message=error_msg)
                    print(f"[SET_ACTION] Job {job_id} marked as FAILED")
            
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'httpStatus': response.status_code,
                'job_id': job_id
            }), response.status_code
            
    except requests.exceptions.Timeout:
        # Log failed action on timeout
        if action_type and customer_ids:
            error_msg = 'Request timeout after 30s'
            print(f"[SET_ACTION] TIMEOUT: user={user_id}, action={action_type}")
            log_user_action(
                user_id=user_id,
                action_type=action_type,
                customer_ids=customer_ids,
                ip_address=get_client_ip(request),
                status='failure',
                error_message=error_msg
            )
            
            # UPDATE job to FAILED
            if job_id:
                update_job(job_id=job_id, status='FAILED', http_status=None,
                          error_message=error_msg)
                print(f"[SET_ACTION] Job {job_id} marked as FAILED (timeout)")
        
        return jsonify({
            'status': 'error',
            'message': 'Request timeout',
            'httpStatus': 408,
            'job_id': job_id
        }), 408
    except requests.exceptions.RequestException as e:
        # Log failed action on request exception
        if action_type and customer_ids:
            error_msg = str(e)
            print(f"[SET_ACTION] REQUEST_ERROR: user={user_id}, action={action_type}, error={error_msg}")
            log_user_action(
                user_id=user_id,
                action_type=action_type,
                customer_ids=customer_ids,
                ip_address=get_client_ip(request),
                status='failure',
                error_message=error_msg
            )
            
            # UPDATE job to FAILED
            if job_id:
                update_job(job_id=job_id, status='FAILED', http_status=None,
                          error_message=error_msg)
                print(f"[SET_ACTION] Job {job_id} marked as FAILED (request error)")
        
        return jsonify({
            'status': 'error',
            'message': str(e),
            'httpStatus': 500,
            'job_id': job_id
        }), 500
    except Exception as e:
        # Log failed action on unexpected error
        if action_type and customer_ids:
            error_msg = str(e)
            print(f"[SET_ACTION] EXCEPTION: user={user_id}, action={action_type}, error={error_msg}")
            log_user_action(
                user_id=user_id,
                action_type=action_type,
                customer_ids=customer_ids,
                ip_address=get_client_ip(request),
                status='failure',
                error_message=error_msg
            )
            
            # UPDATE job to FAILED
            if job_id:
                update_job(job_id=job_id, status='FAILED', http_status=None,
                          error_message=error_msg)
                print(f"[SET_ACTION] Job {job_id} marked as FAILED (exception)")
        
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}',
            'httpStatus': 500,
            'job_id': job_id
        }), 500


@app.route('/api/appstatus/<customer_id>')
@require_auth
@audit_action('T-Enable')
def get_app_status(customer_id):
    """API endpoint to get app status for a customer"""
    # Demo app status data
    demo_statuses = [
        {"app_name": "dpp", "status": "Ready"},
        {"app_name": "kms", "status": "Ready"},
        {"app_name": "oto-oms", "status": "Ready"},
        {"app_name": "scb", "status": "Ready"},
        {"app_name": "ucc", "status": "Ready"},
        {"app_name": "wids", "status": "Transiting"},
        {"app_name": "airgroup", "status": "unknown-Failed to track ack"},
        {"app_name": "airmatch", "status": "Failure", "reason": "Device config missing"},
    ]
    return jsonify(demo_statuses)


# ============================================================================
# AUDIT TRAIL ROUTES
# ============================================================================

@app.route('/api/audit/trail', methods=['GET'])
@require_auth
def get_audit_trail_api():
    """Get audit trail with optional filters"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)  # Max 500 records
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        customer_id = request.args.get('customer_id')
        
        records = get_audit_trail(
            limit=limit,
            user_id=user_id,
            action_type=action_type,
            customer_id=customer_id
        )
        
        return jsonify({
            'success': True,
            'count': len(records),
            'records': records
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/audit/customer/<customer_id>', methods=['GET'])
@require_auth
def get_customer_audit(customer_id):
    """Get audit trail for a specific customer"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        records = get_customer_actions(customer_id, limit=limit)
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'count': len(records),
            'records': records
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/audit/user/<username>', methods=['GET'])
@require_auth
def get_user_audit(username):
    """Get audit trail for a specific user"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        records = get_user_actions(username, limit=limit)
        
        return jsonify({
            'success': True,
            'username': username,
            'count': len(records),
            'records': records
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/audit/stats', methods=['GET'])
@require_auth
def get_audit_stats_api():
    """Get audit trail statistics"""
    try:
        stats = get_audit_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================================================
# JOB MANAGEMENT ROUTES (Phase 1: Job Creation & Retrieval)
# ============================================================================

@app.route('/api/jobs/create', methods=['POST'])
@require_auth
def create_job_endpoint():
    """
    Create a new job after Set Action succeeds
    
    Expected request body:
    {
        'action_code': int (1-6),
        'action_name': str ('tran-begin', 'pe-enable', etc),
        'cids': list of customer IDs,
        'cluster_url': str (optional),
        'batch_id': str (optional),
        'request_payload': dict (optional),
        'response_summary': str (optional)
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate required fields
        action_code = data.get('action_code')
        action_name = data.get('action_name')
        cids = data.get('cids', [])
        
        if not action_code or not action_name:
            return jsonify({
                'success': False,
                'message': 'action_code and action_name are required'
            }), 400
        
        if not isinstance(cids, list) or len(cids) == 0:
            return jsonify({
                'success': False,
                'message': 'cids must be a non-empty list'
            }), 400
        
        # Optional fields
        cluster_url = data.get('cluster_url')
        batch_id = data.get('batch_id')
        request_payload = data.get('request_payload')
        response_summary = data.get('response_summary')
        
        # Create the job
        job = create_job(
            user_id=user_id,
            action_code=action_code,
            action_name=action_name,
            cids=cids,
            cluster_url=cluster_url,
            batch_id=batch_id,
            request_payload=request_payload,
            response_summary=response_summary
        )
        
        if not job:
            return jsonify({
                'success': False,
                'message': 'Failed to create job'
            }), 500
        
        print(f"[JOBS] Created job for user {user_id}: {job['job_id']}")
        
        return jsonify({
            'success': True,
            'message': 'Job created successfully',
            'job': job
        }), 201
        
    except Exception as e:
        print(f"[JOBS] ERROR in create_job_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/jobs/mine', methods=['GET'])
@require_auth
def get_user_jobs_endpoint():
    """
    Get all jobs for the logged-in user, ordered by newest first
    
    Query parameters:
        limit (int, optional): Max jobs to return (default: 50, max: 500)
    """
    try:
        user_id = session.get('user_id')
        limit = min(int(request.args.get('limit', 50)), 500)
        
        jobs = get_user_jobs(user_id, limit=limit)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'job_count': len(jobs),
            'jobs': jobs
        }), 200
        
    except Exception as e:
        print(f"[JOBS] ERROR in get_user_jobs_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/customers', methods=['GET'])
@require_auth
def get_job_customers_endpoint(job_id):
    """
    Get all customer IDs for a specific job
    
    Returns:
        {
            'success': bool,
            'job_id': str,
            'customer_count': int,
            'customers': [list of CIDs]
        }
    """
    try:
        user_id = session.get('user_id')
        
        # Get job details to verify ownership
        job = get_job_details(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': f'Job not found: {job_id}'
            }), 404
        
        # Verify user owns this job
        if job['user_id'] != user_id:
            print(f"[JOBS] Access denied: user {user_id} tried to access job owned by {job['user_id']}")
            return jsonify({
                'success': False,
                'message': 'Access denied: job belongs to another user'
            }), 403
        
        # Get customers for this job
        customers = get_job_customers(job_id)
        
        print(f"[JOBS] Retrieved {len(customers)} customers for job {job_id}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'customer_count': len(customers),
            'customers': customers
        }), 200
        
    except Exception as e:
        print(f"[JOBS] ERROR in get_job_customers_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/actions', methods=['GET'])
@require_auth
def get_job_actions_endpoint(job_id):
    """
    Fetch upstream GET /tms/v1/get/action?cid=ALL and filter to only job's CIDs
    
    Query parameters:
        token (str, required): Bearer token for upstream API
        cluster_url (str, required): Base URL of the cluster (e.g., https://cnx-apigw-...)
    
    Returns:
        {
            'success': bool,
            'job_id': str,
            'customer_count': int,
            'actions': { "cid": {"action_code": int, "action_desc": str}, ... }
        }
    """
    try:
        user_id = session.get('user_id')
        
        # Get job details to verify ownership
        job = get_job_details(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': f'Job not found: {job_id}'
            }), 404
        
        # Verify user owns this job
        if job['user_id'] != user_id:
            print(f"[JOBS] Access denied: user {user_id} tried to access job owned by {job['user_id']}")
            return jsonify({
                'success': False,
                'message': 'Access denied: job belongs to another user'
            }), 403
        
        # Get token and cluster URL from query params
        token = request.args.get('token')
        cluster_url = request.args.get('cluster_url')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'token query parameter is required'
            }), 400
        
        if not cluster_url:
            return jsonify({
                'success': False,
                'message': 'cluster_url query parameter is required'
            }), 400
        
        # Get customers for this job
        job_cids = get_job_customers(job_id)
        if not job_cids:
            return jsonify({
                'success': True,
                'job_id': job_id,
                'customer_count': 0,
                'actions': {}
            }), 200
        
        # Normalize cluster URL
        cluster_url = cluster_url.rstrip('/')
        
        # Fetch upstream: GET /tms/v1/get/action?cid=ALL
        upstream_url = f'{cluster_url}/tms/v1/get/action?cid=ALL'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"[JOBS] Fetching upstream actions from {upstream_url}")
        
        response = requests.get(upstream_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            error_msg = f'Upstream API returned {response.status_code}: {response.text[:200]}'
            print(f"[JOBS] ERROR: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), response.status_code
        
        # Parse upstream response
        try:
            all_actions = response.json()
        except ValueError as e:
            error_msg = f'Invalid JSON from upstream: {str(e)}'
            print(f"[JOBS] ERROR: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500
        
        # Filter to only job's CIDs
        job_cid_set = set(job_cids)
        filtered_actions = {
            cid: action_data 
            for cid, action_data in all_actions.items() 
            if cid in job_cid_set
        }
        
        print(f"[JOBS] Filtered {len(all_actions)} upstream results to {len(filtered_actions)} job customers")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'customer_count': len(filtered_actions),
            'actions': filtered_actions
        }), 200
        
    except requests.exceptions.Timeout:
        error_msg = 'Upstream request timed out'
        print(f"[JOBS] ERROR: {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        }), 504
        
    except requests.exceptions.RequestException as e:
        error_msg = f'Network error contacting upstream: {str(e)}'
        print(f"[JOBS] ERROR: {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        }), 503
        
    except Exception as e:
        print(f"[JOBS] ERROR in get_job_actions_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# PHASE 3: APP STATUS CACHING
# ============================================================================

@app.route('/api/jobs/<job_id>/appstatus', methods=['GET'])
@require_auth
def get_job_appstatus_endpoint(job_id):
    """
    Fetch app status for a job's customers with caching
    
    Query parameters:
        token (str, required): Bearer token for upstream API
        cluster_url (str, required): Base URL of the cluster
        app (str, optional): App name to query (default 'ALL')
        ttl_seconds (int, optional): Cache TTL in seconds (default 1800 = 30 min)
        skip_cache (bool, optional): Set to 'true' to bypass cache
    
    Returns:
        {
            'success': bool,
            'job_id': str,
            'customer_count': int,
            'cache_hits': int,
            'cache_misses': int,
            'appstatus': {
                'cid': {
                    'app': str,
                    'status': str,
                    'from_cache': bool
                },
                ...
            }
        }
    """
    try:
        user_id = session.get('user_id')
        
        # Get job details to verify ownership
        job = get_job_details(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': f'Job not found: {job_id}'
            }), 404
        
        # Verify user owns this job
        if job['user_id'] != user_id:
            print(f"[APPSTATUS] Access denied: user {user_id} tried to access job owned by {job['user_id']}")
            return jsonify({
                'success': False,
                'message': 'Access denied: job belongs to another user'
            }), 403
        
        # Get parameters
        token = request.args.get('token')
        cluster_url = request.args.get('cluster_url')
        app_name = request.args.get('app', 'ALL')
        ttl_seconds = int(request.args.get('ttl_seconds', 1800))
        skip_cache = request.args.get('skip_cache', 'false').lower() == 'true'
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'token query parameter is required'
            }), 400
        
        if not cluster_url:
            return jsonify({
                'success': False,
                'message': 'cluster_url query parameter is required'
            }), 400
        
        # Get customers for this job
        job_cids = get_job_customers(job_id)
        if not job_cids:
            return jsonify({
                'success': True,
                'job_id': job_id,
                'customer_count': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'appstatus': {}
            }), 200
        
        print(f"[APPSTATUS] Fetching app status for job {job_id}: {len(job_cids)} customers, app={app_name}")
        
        # Check cache for all CIDs
        appstatus_result = {}
        cache_hits = 0
        cache_misses = 0
        
        if not skip_cache:
            # Try to get from cache
            cache_result = get_cached_appstatus_batch(job_cids, app_name, ttl_seconds)
            cache_hits = cache_result['hit_count']
            cache_misses = cache_result['miss_count']
            
            # Add cache hits to result
            for cid, status_data in cache_result['hits'].items():
                appstatus_result[cid] = {
                    'app': app_name,
                    'status': status_data.get('status', 'unknown'),
                    'from_cache': True
                }
            
            job_cids_to_fetch = cache_result['misses']
        else:
            job_cids_to_fetch = job_cids
            print(f"[APPSTATUS] Cache bypassed by request")
        
        # Fetch missing CIDs from upstream (if any)
        if job_cids_to_fetch:
            print(f"[APPSTATUS] Fetching {len(job_cids_to_fetch)} CIDs from upstream")
            
            cluster_url = cluster_url.rstrip('/')
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Try batch fetch first (if upstream supports app?ALL&cid=ALL)
            batch_success = False
            try:
                # Try batch format: /tms/v1/get/appstatus?app=<app>&cid=<cid1>,<cid2>,...
                cid_list = ','.join(job_cids_to_fetch)
                upstream_url = f'{cluster_url}/tms/v1/get/appstatus?app={app_name}&cid={cid_list}'
                
                print(f"[APPSTATUS] Trying batch fetch: {upstream_url[:100]}...")
                response = requests.get(upstream_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    try:
                        batch_data = response.json()
                        
                        if isinstance(batch_data, dict):
                            # Cache and add results
                            for cid, status_data in batch_data.items():
                                if cid in job_cids_to_fetch:
                                    cache_appstatus(cid, status_data, app_name, ttl_seconds)
                                    appstatus_result[cid] = {
                                        'app': app_name,
                                        'status': status_data.get('status', 'unknown'),
                                        'from_cache': False
                                    }
                            
                            batch_success = True
                            print(f"[APPSTATUS] Batch fetch succeeded: {len(batch_data)} results")
                        
                    except Exception as e:
                        print(f"[APPSTATUS] Batch parse error: {str(e)}")
                        batch_success = False
            
            except Exception as e:
                print(f"[APPSTATUS] Batch fetch failed: {str(e)}")
                batch_success = False
            
            # If batch failed, try single CID fetching
            if not batch_success:
                print(f"[APPSTATUS] Falling back to single CID fetch for {len(job_cids_to_fetch)} CIDs")
                
                for cid in job_cids_to_fetch:
                    try:
                        single_url = f'{cluster_url}/tms/v1/get/appstatus?app={app_name}&cid={cid}'
                        response = requests.get(single_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            try:
                                status_data = response.json()
                                cache_appstatus(cid, status_data, app_name, ttl_seconds)
                                appstatus_result[cid] = {
                                    'app': app_name,
                                    'status': status_data.get('status', 'unknown'),
                                    'from_cache': False
                                }
                            except:
                                appstatus_result[cid] = {
                                    'app': app_name,
                                    'status': 'fetch_error',
                                    'from_cache': False
                                }
                        else:
                            appstatus_result[cid] = {
                                'app': app_name,
                                'status': f'http_{response.status_code}',
                                'from_cache': False
                            }
                    
                    except requests.exceptions.Timeout:
                        appstatus_result[cid] = {
                            'app': app_name,
                            'status': 'timeout',
                            'from_cache': False
                        }
                    
                    except Exception as e:
                        appstatus_result[cid] = {
                            'app': app_name,
                            'status': 'error',
                            'from_cache': False
                        }
                
                print(f"[APPSTATUS] Single fetch completed: {len(appstatus_result)} CIDs processed")
        
        # Cleanup expired cache periodically
        cleanup_expired_cache(ttl_seconds)
        
        print(f"[APPSTATUS] Returning {len(appstatus_result)} CIDs (hits: {cache_hits}, misses: {cache_misses})")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'customer_count': len(job_cids),
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'appstatus': appstatus_result
        }), 200
        
    except Exception as e:
        print(f"[APPSTATUS] ERROR in get_job_appstatus_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/cache/stats', methods=['GET'])
@require_auth
def get_cache_stats_endpoint():
    """
    Get cache statistics for debugging and monitoring
    
    Returns:
        {
            'success': bool,
            'stats': {
                'total_entries': int,
                'unique_cids': int,
                'size_bytes': int,
                'size_kb': float
            }
        }
    """
    try:
        stats = get_cache_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"[CACHE] ERROR getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/cache/invalidate', methods=['POST'])
@require_auth
def invalidate_cache_endpoint():
    """
    Invalidate cache entries (admin only)
    
    Request body:
    {
        'cid': str (optional),
        'app': str (optional),
        'clear_all': bool (optional)
    }
    
    Returns:
        {
            'success': bool,
            'rows_deleted': int
        }
    """
    try:
        data = request.get_json() or {}
        cid = data.get('cid')
        app_name = data.get('app')
        clear_all = data.get('clear_all', False)
        
        if clear_all:
            deleted = invalidate_appstatus_cache()
            print(f"[CACHE] Cache cleared: {deleted} rows")
        else:
            deleted = invalidate_appstatus_cache(cid=cid, app_name=app_name)
        
        return jsonify({
            'success': True,
            'rows_deleted': deleted
        }), 200
        
    except Exception as e:
        print(f"[CACHE] ERROR invalidating cache: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/health')


def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "TMS Dashboard"})


# ============================================================================
# PROD CUSTOMER DATA ROUTES
# ============================================================================

@app.route('/api/prod-customer-data/run', methods=['POST'])
@require_admin
def run_prod_customer_data():
    """
    Run prod customer data fetch and store results.
    
    Supports multiple input sources:
    1. customer_ids (list) - Pre-parsed customer IDs
    2. csv_content (str) - CSV content to parse
    3. manual_entry (str) - Manual text entry (comma or line-separated)
    
    Expected request body:
    {
        'data_source_url': str (required),
        'cluster': str (required),
        'device_type': str (required),
        'customer_ids': list (optional - pre-parsed IDs),
        'csv_content': str (optional - raw CSV content),
        'manual_entry': str (optional - comma or line-separated IDs),
        'total_devices': int (optional - for batch generation calculations)
    }
    
    Returns:
        {
            'success': bool,
            'total_customers': int,
            'total_devices': int,
            'customer_ids': list,
            'error': str (if applicable)
        }
    """
    try:
        from src.prod_customer_data import normalize_customer_ids, parse_csv_input, parse_manual_entry
        
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        data_source_url = data.get('data_source_url', '').strip()
        cluster = data.get('cluster', '').strip()
        device_type = data.get('device_type', '').strip()
        customer_ids = data.get('customer_ids', [])
        csv_content = data.get('csv_content', '').strip()
        manual_entry = data.get('manual_entry', '').strip()
        total_devices = data.get('total_devices', 0)
        
        if not cluster or not device_type:
            return jsonify({
                'error': 'cluster and device_type are required'
            }), 400
        
        print(f"[PROD-DATA] Run request: cluster={cluster}, device={device_type}, source={data_source_url}")
        
        # Priority-based source selection: customer_ids > csv > manual_entry
        if customer_ids and isinstance(customer_ids, list) and len(customer_ids) > 0:
            # Pre-parsed customer IDs (typically from API)
            print(f"[PROD-DATA] Using pre-parsed customer IDs ({len(customer_ids)} IDs)")
            customer_ids = normalize_customer_ids(customer_ids)
        elif csv_content:
            # Parse CSV content
            print(f"[PROD-DATA] Parsing CSV content (length: {len(csv_content)} chars)")
            customer_ids = parse_csv_input(csv_content)
        elif manual_entry:
            # Parse manual entry
            print(f"[PROD-DATA] Parsing manual entry (length: {len(manual_entry)} chars)")
            customer_ids = parse_manual_entry(manual_entry)
        else:
            return jsonify({
                'error': 'Please provide Customer IDs via API, CSV, or manual entry.'
            }), 400
        
        if not customer_ids or len(customer_ids) == 0:
            return jsonify({
                'error': 'No valid customer IDs found in the provided input.'
            }), 400
        
        print(f"[PROD-DATA] Extracted {len(customer_ids)} customer IDs after normalization")
        
        # If total_devices not provided, estimate based on customer count
        if not total_devices or total_devices <= 0:
            total_devices = len(customer_ids) * 2  # Default estimate: 2 devices per customer
        
        # Save to database
        result = save_prod_customer_data(
            cluster=cluster,
            device_type=device_type,
            data_source_url=data_source_url,
            customer_ids=customer_ids,
            total_devices=total_devices,
            username=user_id
        )
        
        if not result['success']:
            return jsonify({
                'error': f"Database error: {result.get('error', 'Unknown error')}"
            }), 500
        
        print(f"[PROD-DATA] Saved {result['total_customers']} customers and {total_devices} devices for {cluster}/{device_type}")
        
        return jsonify({
            'success': True,
            'total_customers': result['total_customers'],
            'total_devices': total_devices,
            'customer_ids': customer_ids
        }), 200
        
    except Exception as e:
        print(f"[PROD-DATA] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-customer-data/load', methods=['GET'])
@require_auth
def load_prod_customer_data():
    """
    Load saved prod customer data for a specific cluster/device combination
    
    Query parameters:
        cluster (str, required)
        device_type (str, required)
    
    Returns:
        {
            'success': bool,
            'cluster': str,
            'device_type': str,
            'total_customers': int,
            'customer_ids': list,
            'created_at': str,
            'created_by': str,
            'updated_at': str
        }
    """
    try:
        cluster = request.args.get('cluster', '').strip()
        device_type = request.args.get('device_type', '').strip()
        
        if not cluster or not device_type:
            return jsonify({
                'error': 'cluster and device_type query parameters are required'
            }), 400
        
        print(f"[PROD-DATA] Load request: cluster={cluster}, device={device_type}")
        
        data = get_prod_customer_data(cluster, device_type)
        
        if not data:
            return jsonify({
                'success': False,
                'message': f'No saved data for {cluster}/{device_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'cluster': data['cluster'],
            'device_type': data['device_type'],
            'total_customers': data['total_customers'],
            'customer_ids': data['customer_ids'],
            'created_at': data['created_at'],
            'created_by': data['created_by'],
            'updated_at': data['updated_at']
        }), 200
        
    except Exception as e:
        print(f"[PROD-DATA] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-customer-data/metadata', methods=['GET'])
@require_auth
def get_prod_customer_data_metadata():
    """
    Get metadata for stored prod customer data (without customer IDs list)
    
    Query parameters:
        cluster (str, required)
        device_type (str, required)
    
    Returns:
        {
            'success': bool,
            'total_customers': int,
            'created_at': str,
            'created_by': str,
            'updated_at': str
        }
    """
    try:
        cluster = request.args.get('cluster', '').strip()
        device_type = request.args.get('device_type', '').strip()
        
        if not cluster or not device_type:
            return jsonify({
                'error': 'cluster and device_type query parameters are required'
            }), 400
        
        print(f"[PROD-DATA] Metadata request: cluster={cluster}, device={device_type}")
        
        data = get_prod_customer_data(cluster, device_type)
        
        if not data:
            return jsonify({
                'success': False,
                'message': f'No stored data for {cluster}/{device_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'total_customers': data['total_customers'],
            'created_at': data['created_at'],
            'created_by': data['created_by'],
            'updated_at': data['updated_at']
        }), 200
        
    except Exception as e:
        print(f"[PROD-DATA] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-customer-data/all', methods=['GET'])
@require_auth
def get_all_prod_customer_data_endpoint():
    """Get all saved prod customer data records"""
    try:
        data_list = get_all_prod_customer_data()
        
        return jsonify({
            'success': True,
            'count': len(data_list),
            'records': data_list
        }), 200
        
    except Exception as e:
        print(f"[PROD-DATA] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-customer-data/delete', methods=['POST'])
@require_auth
def delete_prod_customer_data_endpoint():
    """
    Delete saved prod customer data
    
    Expected request body:
    {
        'cluster': str,
        'device_type': str
    }
    """
    try:
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        cluster = data.get('cluster', '').strip()
        device_type = data.get('device_type', '').strip()
        
        if not cluster or not device_type:
            return jsonify({
                'error': 'cluster and device_type are required'
            }), 400
        
        print(f"[PROD-DATA] Delete request by {user_id}: cluster={cluster}, device={device_type}")
        
        result = delete_prod_customer_data(cluster, device_type)
        
        if not result['success']:
            return jsonify({
                'error': f"Delete failed: {result.get('error', 'Unknown error')}"
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Deleted {cluster}/{device_type}'
        }), 200
        
    except Exception as e:
        print(f"[PROD-DATA] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-batch/check-stored', methods=['GET'])
@require_auth
def check_stored_for_batch():
    """
    Check if stored customer/device data exists for a cluster/device combo.
    Returns metadata needed for batch generation.
    
    Query parameters:
        cluster (str, required)
        device_selection (str, required)
    """
    try:
        cluster = request.args.get('cluster', '').strip()
        device_selection = request.args.get('device_selection', '').strip()
        
        if not cluster or not device_selection:
            return jsonify({
                'error': 'cluster and device_selection parameters are required'
            }), 400
        
        print(f"[BATCH] Check stored: cluster={cluster}, device={device_selection}")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import get_prod_customer_data
        
        data = get_prod_customer_data(cluster, device_selection)
        
        if not data:
            return jsonify({
                'success': False,
                'found': False,
                'message': f'No stored data found for {cluster} / {device_selection}. Please run Prod Customer Data first.'
            }), 404
        
        return jsonify({
            'success': True,
            'found': True,
            'total_customers': data['total_customers'],
            'total_devices': data.get('total_devices', 0),
            'customer_ids': data['customer_ids']
        }), 200
        
    except Exception as e:
        print(f"[BATCH] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-batch/generate', methods=['POST'])
@require_admin
def generate_batches_endpoint():
    """
    Generate and save batches for a cluster/device combination.
    
    Expected request body:
    {
        'cluster': str,
        'device_selection': str,
        'device_cap': int,
        'total_customers': int,
        'total_devices': int,
        'customer_ids': [list of IDs]
    }
    """
    try:
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        cluster = data.get('cluster', '').strip()
        device_selection = data.get('device_selection', '').strip()
        device_cap = data.get('device_cap')
        total_customers = data.get('total_customers')
        total_devices = data.get('total_devices')
        customer_ids = data.get('customer_ids', [])
        
        # Validation
        if not cluster or not device_selection:
            return jsonify({
                'error': 'cluster and device_selection are required'
            }), 400
        
        if not isinstance(device_cap, (int, float)) or device_cap < 1:
            return jsonify({
                'error': 'device_cap must be a positive integer'
            }), 400
        
        if not isinstance(total_customers, int) or total_customers < 1:
            return jsonify({
                'error': 'total_customers must be a positive integer'
            }), 400
        
        if not isinstance(total_devices, int) or total_devices < 1:
            return jsonify({
                'error': 'total_devices must be a positive integer'
            }), 400
        
        if not isinstance(customer_ids, list) or len(customer_ids) == 0:
            return jsonify({
                'error': 'customer_ids must be a non-empty list'
            }), 400
        
        print(f"[BATCH] Generate request by {user_id}: cluster={cluster}, device={device_selection}, cap={device_cap}")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import generate_and_save_batches
        
        result = generate_and_save_batches(
            cluster=cluster,
            device_selection=device_selection,
            device_cap=device_cap,
            customer_ids=customer_ids,
            total_customers=total_customers,
            total_devices=total_devices,
            username=user_id
        )
        
        if not result['success']:
            return jsonify({
                'error': f"Generation failed: {result.get('error', 'Unknown error')}"
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Generated {result["total_batches"]} batch(es)',
            'total_batches': result['total_batches'],
            'customers_per_batch': result['customers_per_batch'],
            'avg_devices': result['avg_devices'],
            'batch_ids': result['batch_ids']
        }), 200
        
    except Exception as e:
        print(f"[BATCH] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-batch/list', methods=['GET'])
@require_auth
def list_batches_endpoint():
    """
    List all batches for a cluster/device combination.
    
    Query parameters:
        cluster (str, required)
        device_selection (str, required)
    """
    try:
        cluster = request.args.get('cluster', '').strip()
        device_selection = request.args.get('device_selection', '').strip()
        
        if not cluster or not device_selection:
            return jsonify({
                'error': 'cluster and device_selection parameters are required'
            }), 400
        
        print(f"[BATCH] List request: cluster={cluster}, device={device_selection}")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import get_batches_for_cluster_device
        
        batches = get_batches_for_cluster_device(cluster, device_selection)
        
        return jsonify({
            'success': True,
            'batches': batches,
            'total_batches': len(batches)
        }), 200
        
    except Exception as e:
        print(f"[BATCH] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/prod-batch/delete', methods=['POST'])
@require_admin
def delete_batches_endpoint():
    """
    Delete all batches for a specific cluster/device combination.
    
    Expected request body:
    {
        'cluster': str,
        'device_selection': str
    }
    """
    try:
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        cluster = data.get('cluster', '').strip()
        device_selection = data.get('device_selection', '').strip()
        
        if not cluster or not device_selection:
            return jsonify({
                'error': 'cluster and device_selection are required'
            }), 400
        
        print(f"[BATCH] Delete request by {user_id}: cluster={cluster}, device={device_selection}")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import delete_all_batches_for_cluster_device
        
        result = delete_all_batches_for_cluster_device(cluster, device_selection)
        
        if not result['success']:
            return jsonify({
                'error': f"Delete failed: {result.get('error', 'Unknown error')}"
            }), 500
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Batches deleted'),
            'deleted_count': result.get('deleted_count', 0)
        }), 200
        
    except Exception as e:
        print(f"[BATCH] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/batches/assign', methods=['POST'])
@require_auth
def assign_batch_endpoint():
    """
    Assign a batch to the current user (atomic operation).
    
    Expected request body:
    {
        'batch_id': str
    }
    
    Returns success if batch was unassigned, error if already assigned.
    """
    try:
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        batch_id = data.get('batch_id', '').strip()
        
        if not batch_id:
            return jsonify({
                'error': 'batch_id is required'
            }), 400
        
        print(f"[BATCH] Assign request by {user_id}: batch_id={batch_id}")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import assign_batch_to_user
        
        result = assign_batch_to_user(batch_id, user_id)
        
        if not result['success']:
            return jsonify({
                'error': result.get('error', 'Assignment failed')
            }), 400
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Batch assigned'),
            'batch_id': batch_id
        }), 200
        
    except Exception as e:
        print(f"[BATCH] Assign ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/batches/assign-bulk', methods=['POST'])
@require_auth
def assign_batches_bulk_endpoint():
    """
    Assign multiple batches to the current user (atomic per-batch operation).
    
    Expected request body:
    {
        'batch_ids': [str, str, ...]
    }
    
    Returns:
        - assigned: list of successfully assigned batch IDs
        - skipped: list of dicts with {batch_id, reason}
        - message: summary message
    """
    try:
        user_id = session.get('user_id', 'unknown')
        data = request.get_json()
        
        batch_ids = data.get('batch_ids', [])
        
        if not isinstance(batch_ids, list) or len(batch_ids) == 0:
            return jsonify({
                'error': 'batch_ids must be a non-empty list'
            }), 400
        
        print(f"[BATCH] Bulk assign request by {user_id}: {len(batch_ids)} batches")
        
        # Import here to avoid circular imports
        from src.prod_customer_data import assign_batches_bulk
        
        result = assign_batches_bulk(batch_ids, user_id)
        
        if not result['success']:
            return jsonify({
                'error': result.get('error', 'Bulk assignment failed')
            }), 400
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Batches assigned'),
            'assigned': result.get('assigned', []),
            'skipped': result.get('skipped', [])
        }), 200
        
    except Exception as e:
        print(f"[BATCH] Bulk Assign ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/batches/assigned', methods=['GET'])
@require_auth
def list_assigned_batches():
    """
    List all batches assigned to current user for a given cluster/device.
    
    Query parameters:
        cluster (str, required)
        device (str, required)
    
    Returns:
        batches: list of batches where assigned_to == current_user
        count: total number of assigned batches
    """
    try:
        user_id = session.get('user_id', 'unknown')
        cluster = request.args.get('cluster', '').strip()
        device = request.args.get('device', '').strip()
        
        if not cluster or not device:
            return jsonify({
                'error': 'cluster and device parameters are required'
            }), 400
        
        print(f"[ASSIGNED] List request for user {user_id}: cluster={cluster}, device={device}")
        
        from src.prod_customer_data import get_batches_for_cluster_device
        
        all_batches = get_batches_for_cluster_device(cluster, device)
        
        # Filter to only batches assigned to current user
        assigned_batches = [b for b in all_batches if b.get('assigned_to') == user_id]
        
        # Ensure customer_count field is present in response
        for batch in assigned_batches:
            # Use customers_in_batch from backend (which already handles fallback)
            # But ensure it's not 0, otherwise fall back to customer_ids length
            customers_in_batch = batch.get('customers_in_batch', 0)
            customer_ids = batch.get('customer_ids', [])
            batch['customer_count'] = customers_in_batch if customers_in_batch > 0 else len(customer_ids)
        
        return jsonify({
            'success': True,
            'batches': assigned_batches,
            'count': len(assigned_batches)
        }), 200
        
    except Exception as e:
        print(f"[ASSIGNED] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/batches/<batch_id>/customers', methods=['GET'])
@require_auth
def get_batch_customers(batch_id):
    """
    Get customer IDs for a specific batch.
    
    Returns:
        customer_ids: list of customer IDs
        count: total number of customers
    """
    try:
        from src.prod_customer_data import get_batch_by_id
        
        print(f"[BATCH_CUSTOMERS] Fetch request for batch: {batch_id}")
        
        batch = get_batch_by_id(batch_id)
        
        if not batch:
            return jsonify({
                'error': f'Batch {batch_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'batch_id': batch['batch_id'],
            'customer_ids': batch['customer_ids'],
            'count': len(batch['customer_ids'])
        }), 200
        
    except Exception as e:
        print(f"[BATCH_CUSTOMERS] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/batches/<batch_id>/customers.csv', methods=['GET'])
@require_auth
def download_batch_customers_csv(batch_id):
    """
    Download customer IDs for a specific batch as CSV.
    
    Returns:
        CSV file with Content-Type: text/csv
        Format:
            cust_id
            CUST001
            CUST002
            ...
    """
    try:
        from src.prod_customer_data import get_batch_by_id
        import csv
        from io import StringIO
        
        print(f"[CSV] Download request for batch: {batch_id}")
        
        batch = get_batch_by_id(batch_id)
        
        if not batch:
            return jsonify({
                'error': f'Batch {batch_id} not found'
            }), 404
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['cust_id'])
        
        # Write customer IDs
        for customer_id in batch['customer_ids']:
            writer.writerow([customer_id])
        
        csv_content = output.getvalue()
        
        # Send CSV file as download
        return app.response_class(
            response=csv_content,
            status=200,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{batch_id}_customers.csv"'
            }
        )
        
    except Exception as e:
        print(f"[CSV] ERROR: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/user/role', methods=['GET'])
@require_auth
def get_user_role():
    """Get current user's role (admin or regular)"""
    return jsonify({
        'is_admin': is_admin_user(),
        'user_id': get_current_user()
    }), 200


@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """
    Get list of all available clusters from database
    Returns clusters ordered by display_order
    """
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'prod_customer_data.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, code, name, description, status, display_order 
            FROM clusters 
            WHERE status = 'ACTIVE'
            ORDER BY display_order
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        clusters = []
        for row in rows:
            clusters.append({
                'id': row['id'],
                'code': row['code'],
                'name': row['name'],
                'description': row['description'],
                'status': row['status'],
                'display_order': row['display_order']
            })
        
        return jsonify({
            'success': True,
            'data': clusters,
            'count': len(clusters)
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch clusters: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """
    Get list of all available devices from database
    Returns devices ordered by display_order
    """
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'prod_customer_data.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, code, name, description, device_capacity, status, display_order 
            FROM devices 
            WHERE status = 'ACTIVE'
            ORDER BY display_order
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        devices = []
        for row in rows:
            devices.append({
                'id': row['id'],
                'code': row['code'],
                'name': row['name'],
                'description': row['description'],
                'device_capacity': row['device_capacity'],
                'status': row['status'],
                'display_order': row['display_order']
            })
        
        return jsonify({
            'success': True,
            'data': devices,
            'count': len(devices)
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"\n{'='*60}")
    print(f"  TMS Dashboard Server Starting")
    print(f"{'='*60}")
    print(f"  🌐 Access URL: http://localhost:{port}")
    print(f"  🌐 Network:    http://0.0.0.0:{port}")
    print(f"  ⚡ Threading:  Enabled (multi-user support)")
    print(f"  ✅ Status:     Running")
    print(f"{'='*60}\n")
    
    # Disable debug reloader in background runs to avoid duplicate processes
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
