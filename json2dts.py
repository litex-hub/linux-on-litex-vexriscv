#!/usr/bin/env python3

import sys
import json
import argparse

parser = argparse.ArgumentParser(description="LiteX's CSR JSON to Linux DTS generator")
parser.add_argument("csr_json", help="CSR JSON file")
args = parser.parse_args()

d = json.load(open(args.csr_json))

kB = 1024
mB = kB*1024

aliases = {}

# Header -------------------------------------------------------------------------------------------

dts = """
/dts-v1/;

/ {
	#address-cells = <0x2>;
	#size-cells = <0x2>;
	compatible = "enjoy-digital,litex-vexriscv-soclinux";
	model = "VexRiscv SoCLinux";
"""

# Boot Arguments -----------------------------------------------------------------------------------

dts += """
	chosen {{
		bootargs = "mem={main_ram_size_mb}M@0x{main_ram_base:x} rootwait console=liteuart earlycon=sbi root=/dev/ram0 init=/sbin/init swiotlb=32";
		linux,initrd-start = <0x{linux_initrd_start:x}>;
		linux,initrd-end   = <0x{linux_initrd_end:x}>;
	}};
""".format(
		main_ram_base=d["memories"]["main_ram"]["base"],
		main_ram_size=d["memories"]["main_ram"]["size"],
		main_ram_size_mb=d["memories"]["main_ram"]["size"]//mB,

		linux_initrd_start=d["memories"]["main_ram"]["base"] + 8*mB,
		linux_initrd_end=d["memories"]["main_ram"]["base"] + 16*mB)

# CPU ----------------------------------------------------------------------------------------------

dts += """
	cpus {{
		#address-cells = <0x1>;
		#size-cells = <0x0>;
		timebase-frequency = <{sys_clk_freq}>;

		cpu@0 {{
			clock-frequency = <0x0>;
			compatible = "spinalhdl,vexriscv", "sifive,rocket0", "riscv";
			d-cache-block-size = <0x40>;
			d-cache-sets = <0x40>;
			d-cache-size = <0x8000>;
			d-tlb-sets = <0x1>;
			d-tlb-size = <0x20>;
			device_type = "cpu";
			i-cache-block-size = <0x40>;
			i-cache-sets = <0x40>;
			i-cache-size = <0x8000>;
			i-tlb-sets = <0x1>;
			i-tlb-size = <0x20>;
			mmu-type = "riscv,sv32";
			reg = <0x0>;
			riscv,isa = "rv32ima";
			sifive,itim = <0x1>;
			status = "okay";
			tlb-split;
		}};
	}};
""".format(sys_clk_freq=int(50e6) if "sim" in d["constants"] else d["constants"]["config_clock_frequency"])

# Memory -------------------------------------------------------------------------------------------

dts += """
	memory@{main_ram_base:x} {{
		device_type = "memory";
		reg = <0x0 0x{main_ram_base:x} 0x1 0x{main_ram_size:x}>;
	}};
""".format(main_ram_base=d["memories"]["main_ram"]["base"],
		   main_ram_size=d["memories"]["main_ram"]["size"])

# SoC ----------------------------------------------------------------------------------------------

dts += """
	soc {
		#address-cells = <0x2>;
		#size-cells = <0x2>;
		compatible = "simple-bus";
		ranges;
"""

	# UART -----------------------------------------------------------------------------------------

if "uart" in d["csr_bases"]:
	aliases["serial0"] = "liteuart0"
	dts += """
		liteuart0: serial@{uart_csr_base:x} {{
			device_type = "serial";
			compatible = "litex,liteuart";
			reg = <0x0 0x{uart_csr_base:x} 0x0 0x100>;
			status = "okay";
		}};
	""".format(uart_csr_base=d["csr_bases"]["uart"])

	# Ethernet MAC ---------------------------------------------------------------------------------

if "ethmac" in d["csr_bases"]:
	dts += """
		mac0: mac@{ethmac_csr_base:x} {{
			compatible = "litex,liteeth";
			reg = <0x0 0x{ethmac_csr_base:x} 0x0 0x7c
				0x0 0x{ethphy_csr_base:x} 0x0 0x0a
				0x0 0x{ethmac_mem_base:x} 0x0 0x2000>;
			tx-fifo-depth = <{ethmac_tx_slots}>;
			rx-fifo-depth = <{ethmac_rx_slots}>;
		}};
	""".format(ethphy_csr_base=d["csr_bases"]["ethphy"],
			   ethmac_csr_base=d["csr_bases"]["ethmac"],
			   ethmac_mem_base=d["memories"]["ethmac"]["base"],
			   ethmac_tx_slots=d["constants"]["ethmac_tx_slots"],
			   ethmac_rx_slots=d["constants"]["ethmac_rx_slots"])

	# Leds -----------------------------------------------------------------------------------------

if "leds" in d["csr_bases"]:
	dts += """
		leds: gpio@{leds_csr_base:x} {{
			compatible = "litex,gpio";
			reg = <0x0 0x{leds_csr_base:x} 0x0 0x4>;
			litex,direction = "out";
			status = "disabled";
		}};
	""".format(leds_csr_base=d["csr_bases"]["leds"])

	# RGB Led --------------------------------------------------------------------------------------

for name in ["rgb_led_r0", "rgb_led_g0", "rgb_led_b0"]:
	if name in d["csr_bases"]:
	    dts += """
		{pwm_name}: pwm@{pwm_csr_base:x} {{
	        compatible = "litex,pwm";
	        reg = <0x0 0x{pwm_csr_base:x} 0x0 0x24>;
	        clock = <100000000>;
	        #pwm-cells = <3>;
	        status = "okay";
	    }};
	""".format(pwm_name=name,
		       pwm_csr_base=d["csr_bases"][name])

	# Switches -------------------------------------------------------------------------------------

if "switches" in d["csr_bases"]:
	dts += """
		switches: gpio@{switches_csr_base:x} {{
			compatible = "litex,gpio";
			reg = <0x0 0x{switches_csr_base:x} 0x0 0x4>;
			litex,direction = "in";
			status = "disabled";
		}};
	""".format(switches_csr_base=d["csr_bases"]["switches"])

	# SPI ------------------------------------------------------------------------------------------

if "spi" in d["csr_bases"]:
    aliases["spi0"] = "litespi0"

    dts += """
	    litespi0: spi@{spi_csr_base:x} {{
		    compatible = "litex,litespi";
		    reg = <0x0 0x{spi_csr_base:x} 0x0 0x100>;
		    status = "okay";

		    litespi,max-bpw = <8>;
		    litespi,sck-frequency = <1000000>;
		    litespi,num-cs = <1>;

		    #address-cells = <0x1>;
		    #size-cells = <0x1>;

		    spidev0: spidev@0 {{
			compatible = "linux,spidev";
			reg = <0 0>;
			spi-max-frequency = <1000000>;
			status = "okay";
		    }};
	    }};
    """.format(spi_csr_base=d["csr_bases"]["spi"])

	# I2C ------------------------------------------------------------------------------------------

if "i2c0" in d["csr_bases"]:
    dts += """
		i2c0: i2c@{i2c0_csr_base:x} {{
			compatible = "litex,i2c";
			reg = <0x0 0x{i2c0_csr_base:x} 0x0 0x5>;
			status = "okay";
		}};
""".format(i2c0_csr_base=d["csr_bases"]["i2c0"])

	# XADC -----------------------------------------------------------------------------------------

if "xadc" in d["csr_bases"]:
    dts += """
		hwmon0: xadc@{xadc_csr_base:x} {{
			compatible = "litex,hwmon-xadc";
			reg = <0x0 0x{xadc_csr_base:x} 0x0 0x20>;
			status = "okay";
		}};
""".format(xadc_csr_base=d["csr_bases"]["xadc"])

	# Framebuffer ----------------------------------------------------------------------------------

if "framebuffer" in d["csr_bases"]:
    # FIXME: dynamic framebuffer base and size
    framebuffer_base   = 0xc8000000
    framebuffer_width  = 1280
    framebuffer_height = 720
    dts += """
		framebuffer0: framebuffer@f0000000 {{
			compatible = "simple-framebuffer";
			reg = <0x0 0x{framebuffer_base:x} 0x0 0x{framebuffer_size:x}>;
			width = <{framebuffer_width}>;
			height = <{framebuffer_height}>;
			stride = <{framebuffer_stride}>;
			format = "a8b8g8r8";
		}};
	""".format(framebuffer_base=framebuffer_base,
               framebuffer_width=framebuffer_width,
               framebuffer_height=framebuffer_height,
               framebuffer_size=framebuffer_width*framebuffer_height*4,
               framebuffer_stride=framebuffer_width*4)

dts += """
	};
"""

# Aliases -----------------------------------------------------------------------------------------

if aliases:
    dts += """
	aliases {
"""
    for alias in aliases:
    	dts += """
	   {} = &{};
""".format(alias, aliases[alias])
    dts += """
	};
"""

dts += """
};
"""

# --------------------------------------------------------------------------------------------------

if "leds" in d["csr_bases"]:
	dts += """
&leds {
	litex,ngpio = <4>;
	status = "okay";
};
	"""

if "switches" in d["csr_bases"]:
	dts += """
&switches {
	litex,ngpio = <4>;
	status = "okay";
};
	"""

print(dts)
