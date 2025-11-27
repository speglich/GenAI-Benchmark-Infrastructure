# GenAI Benchmark Infrastructure

This project provides a complete Terraform infrastructure setup for benchmarking Generative AI models, specifically designed for Oracle Cloud Infrastructure (OCI). It automates the deployment of compute instances with pre-configured benchmarking tools and includes performance comparison capabilities between different AI platforms.

## Features

- **Automated Infrastructure Deployment**: Complete OCI setup with VCN, subnets, security groups, compute instances and IAM policies
- **Pre-configured Benchmarking Environment**: Automatically installs GenAI-Bench and required dependencies
- **Multiple Platform Support**: Benchmarking scripts for both OCI GenAI and vLLM platforms
- **Performance Visualization**: Python scripts for generating comprehensive performance plots and metrics
- **Flexible Instance Configuration**: Support for various compute shapes including GPU instances
- **Security Best Practices**: Proper IAM setup with Instance Principal authentication

## Prerequisites

Before deploying this infrastructure, ensure you have:

- **Oracle Cloud Infrastructure (OCI) Account** with appropriate privileges
- **Terraform** installed (version 1.0+)
- **OCI CLI** configured with proper credentials
- **Valid compartment OCID** and **tenancy OCID**
- **SSH access** capabilities for instance management

## Architecture

The infrastructure creates:

- **Virtual Cloud Network (VCN)** with public and private subnets
- **Internet Gateway** and **NAT Gateway** for connectivity
- **Security Lists** with configurable port exposure
- **Compute Instance** with flexible shape configuration
- **Dynamic Groups** and **IAM Policies** for Instance Principal access
- **Automated software installation** via Ansible playbooks

## Configuration

### Required Variables

Create a `terraform.tfvars` file with the following variables:

```hcl
region = "sa-saopaulo-1"  # Your preferred OCI region
compartment_ocid = "ocid1.compartment.oc1..your-compartment-id"
tenancy_ocid = "ocid1.tenancy.oc1..your-tenancy-id"
```

### Optional Variables

You can customize the deployment by modifying these variables in `terraform.tfvars`:

```hcl
# Instance configuration
shape = "VM.Standard.E5.Flex" # Instance shape
ocpus = 32                    # Number of OCPUs
memory_in_gbs = 64            # Memory allocation
boot_volume_size_in_gbs = 100 # Boot volume size

# Network configuration
exposed_ports = [22]  # Ports to expose

# Image configuration
image_id = "ocid1.image.oc1.sa-saopaulo-1.aaaaaaaa7avt4eh5yycvdmzpenw45offnablkjduihvxhtxoesevvu76n2eq"
ssh_user = "opc"
```

## Deployment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/speglich/GenAI-Benchmark-Infrastructure.git
   cd GenAI-Benchmark-Infrastructure
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Review the deployment plan**:
   ```bash
   terraform plan
   ```

4. **Deploy the infrastructure**:
   ```bash
   terraform apply
   ```

5. **Access your instance**:
   ```bash
   ssh -i ./keys/<environment_name>_private_key.pem opc@<public_ip>
   ```

## Running Benchmarks

The instance comes pre-configured with benchmarking tools. You can run benchmarks using the provided scripts:

### OCI GenAI Benchmark

```bash
cd ~/benchmarks
./oci_benchmark.sh
```

This script benchmarks OCI's Generative AI service with various concurrency levels and traffic scenarios.

### vLLM Benchmark

```bash
cd ~/benchmarks
./vllm_benchmark.sh
```

This script benchmarks vLLM deployments for comparison purposes.

### Generating Performance Plots

After running benchmarks, use the Python plotting script to visualize results:

```bash
cd ~/benchmarks
sh generate_plots.sh
```

The plotting script supports:
- **Multiple platform comparisons**
- **Various performance metrics** (latency, throughput, error rates)
- **Customizable visualizations**
- **CSV export** for further analysis

## Benchmarking Features

### Supported Metrics

- **Time to First Token (TTFT)**

- **End-to-end Latency**
- **Output Throughput** (tokens/second)
- **Input Throughput** (tokens/second)
- **Requests per Second**
- **Error Rates**
- **Token Statistics**

### Traffic Scenarios

The benchmarks support various traffic patterns:
- **Constant load**: `N(5000,0)/(50,0)`
- **Variable load**: `N(480,240)/(300,150)`
- **High throughput**: `N(2200,200)/(200,20)`

### Concurrency Testing

Tests are automatically run with multiple concurrency levels:
- 1, 2, 4, 8, 16, 32, 64, 128, 256 concurrent requests

## 🔧 Customization

### Adding New Benchmarks

1. Create a new shell script in the `benchmarks/` directory
2. Follow the pattern of existing scripts (`oci_benchmark.sh`, `vllm_benchmark.sh`)
3. Use the `genai-bench` command with appropriate parameters

### Modifying Infrastructure

- **Compute Resources**: Adjust `shape`, `ocpus`, and `memory_in_gbs` in variables
- **Network Security**: Modify `exposed_ports` list for different service requirements
- **Storage**: Change `boot_volume_size_in_gbs` for additional disk space
- **Regional Deployment**: Update `region` and `image_id` for different OCI regions

### Custom Ansible Playbooks

Modify `ansible/install_genai_bench.yml` to:
- Install additional software packages
- Configure custom benchmarking tools
- Set up monitoring or logging solutions

## Security Considerations

- **SSH Keys**: Automatically generated and stored in `keys/` directory
- **Instance Principal**: Configured for secure OCI API access
- **Network Security**: Minimal port exposure with customizable security lists
- **IAM Policies**: Least-privilege access for required operations

## Performance Analysis

The included plotting tools provide comprehensive performance analysis:

- **Multi-platform Comparisons**: Compare OCI GenAI vs vLLM performance
- **Scalability Analysis**: Understand performance characteristics across concurrency levels
- **Bottleneck Identification**: Identify performance limitations and optimal configurations
- **Export Capabilities**: CSV export for integration with other analysis tools

## Troubleshooting

### Common Issues

1. **Terraform Apply Fails**:
   - Verify OCI credentials and permissions
   - Check compartment and tenancy OCIDs
   - Ensure sufficient quota for chosen instance shape

2. **SSH Connection Issues**:
   - Verify security group allows SSH (port 22)
   - Check private key permissions (should be 600)
   - Confirm public IP assignment

3. **Benchmark Failures**:
   - Verify Instance Principal configuration
   - Check OCI GenAI service availability in your region
   - Validate API endpoints and model names

### Logs and Debugging

- **Terraform Logs**: Use `TF_LOG=DEBUG terraform apply` for detailed logging
- **Ansible Logs**: Check `/var/log/messages` on the instance for Ansible execution details
- **Benchmark Logs**: Review output files in `~/benchmarks/results/` directory

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add appropriate tests
5. Submit a pull request

## License

This project is provided as-is for educational and benchmarking purposes. Please ensure compliance with Oracle Cloud Infrastructure terms of service and applicable software licenses.

## Support

For issues and questions:
- Check OCI documentation for service-specific issues
- Consult Terraform and Ansible documentation for infrastructure problems

---

**Note**: This infrastructure setup is designed for benchmarking and testing purposes. For production deployments, additional security hardening, monitoring, and backup strategies should be implemented.