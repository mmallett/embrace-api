# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

#installs docker cf and cf container plugin
$bootstrap = <<SCRIPT
apt-get update

apt-get install -y git vim curl wget build-essential python-pip python-dev

cd /vagrant

pip install -r requirements.txt

SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.hostname = 'athena'
  config.vm.box='ubuntu/trusty64'
  # config.vm.box='hashicorp/precise64'
  config.vm.network :private_network, ip: '192.168.50.15'
  config.vm.network 'forwarded_port', guest: 8111, host: 8111
  config.vm.provision 'shell', inline: $bootstrap

end
