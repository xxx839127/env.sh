#!/usr/bin/env python3
import yaml
import subprocess
import os
from pathlib import Path

def configure_sudo(username):
    """Configure passwordless sudo for the user"""
    sudoers_file = f'/etc/sudoers.d/{username}'
    try:
        with open(sudoers_file, 'w') as f:
            f.write(f'{username} ALL=(ALL) NOPASSWD:ALL')
        subprocess.run(['sudo', 'chmod', '440', sudoers_file], check=True)
        return True
    except (IOError, subprocess.CalledProcessError) as e:
        print(f"Error configuring sudo for {username}: {e}")
        return False

def setup_ssh_keys(username):
    """Set up SSH directory and keys with proper permissions"""
    ssh_dir = f'/home/{username}/.ssh'
    try:
        subprocess.run(['sudo', 'mkdir', '-p', ssh_dir], check=True)
        subprocess.run([
            'sudo', 'ssh-keygen', '-t', 'rsa', '-b', '4096', 
            '-f', f'{ssh_dir}/id_rsa', '-N', '""'
        ], check=True)
        subprocess.run(['sudo', 'chown', '-R', f'{username}:{username}', ssh_dir], check=True)
        subprocess.run(['sudo', 'chmod', '700', ssh_dir], check=True)
        subprocess.run(['sudo', 'chmod', '600', f'{ssh_dir}/id_rsa'], check=True)
        subprocess.run(['sudo', 'chmod', '644', f'{ssh_dir}/id_rsa.pub'], check=True)
        
        auth_keys = f'{ssh_dir}/authorized_keys'
        subprocess.run(['sudo', 'touch', auth_keys], check=True)
        subprocess.run(['sudo', 'chmod', '600', auth_keys], check=True)
        subprocess.run(['sudo', 'rm', f'{ssh_dir}/id_rsa.pub'], check=True)
        
        print(f"\nSSH Private Key for {username}:")
        subprocess.run(['sudo', 'cat', f'{ssh_dir}/id_rsa'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error setting up SSH for {username}: {e}")
        return False

def create_shared_project(project_name, usernames):
    """Create and link shared project directories"""
    try:
        # Create root project directory
        root_project_dir = f'/opt/{project_name}'
        subprocess.run(['sudo', 'mkdir', '-p', root_project_dir], check=True)
        subprocess.run(['sudo', 'chown', 'root:root', root_project_dir], check=True)
        subprocess.run(['sudo', 'chmod', '755', root_project_dir], check=True)
        
        # Create public directory
        public_dir = f'{root_project_dir}/public'
        subprocess.run(['sudo', 'mkdir', '-p', public_dir], check=True)
        subprocess.run(['sudo', 'chown', 'root:root', public_dir], check=True)
        subprocess.run(['sudo', 'chmod', '755', public_dir], check=True)
        
        # Create symlinks in each user's home
        for username in usernames:
            user_project_dir = f'/home/{username}/{project_name}'
            subprocess.run(['sudo', 'mkdir', '-p', user_project_dir], check=True)
            subprocess.run(['sudo', 'chown', f'{username}:{username}', user_project_dir], check=True)
            subprocess.run(['sudo', 'chmod', '755', user_project_dir], check=True)
            
            # Create symlink to public directory
            user_public_link = f'{user_project_dir}/public'
            if not Path(user_public_link).exists():
                subprocess.run([
                    'sudo', 'ln', '-s', public_dir, user_public_link
                ], check=True)
            subprocess.run(['sudo', 'chown', f'{username}:{username}', user_public_link], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating shared project: {e}")
        return False

def create_dev_user(username):
    """Create a developer user with all required configurations"""
    try:
        subprocess.run(['sudo', 'useradd', '-m', '-s', '/bin/bash', username], check=True)
        if not configure_sudo(username):
            return False
        if not setup_ssh_keys(username):
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating user {username}: {e}")
        return False

def create_devs(dev_list, project_name=None):
    """Create multiple developer users and shared project"""
    results = {}
    for dev in dev_list:
        print(f"\nCreating environment for developer: {dev}")
        success = create_dev_user(dev)
        results[dev] = "Success" if success else "Failed"
        print(f"{'Successfully' if success else 'Failed to'} create user {dev}")
    
    if project_name:
        print(f"\nCreating shared project: {project_name}")
        if create_shared_project(project_name, dev_list):
            print(f"Successfully created shared project {project_name}")
        else:
            print(f"Failed to create shared project {project_name}")
    
    return results

def load_config():
    """Load configuration from YAML file"""
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
        devs = config.get('devs', '').split(',')
        devs = [d.strip() for d in devs if d.strip()]
        project = config.get('project')
        return devs, project
    except (IOError, yaml.YAMLError) as e:
        print(f"Error loading config: {e}")
        return [], None

def main():
    """Main entry point of the script"""
    devs, project = load_config()
    
    if not devs:
        print("No developers specified in config.yml")
        return
    
    results = create_devs(devs, project)
    
    print("\nSummary of operations:")
    for username, status in results.items():
        print(f"{username}: {status}")

if __name__ == '__main__':
    main()
