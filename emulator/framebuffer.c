#include <generated/csr.h>
#ifdef CSR_FRAMEBUFFER_BASE

#include <stdlib.h>
#include <stdio.h>

#include "framebuffer.h"

struct video_timing {
	unsigned int pixel_clock; /* in tens of kHz */

	unsigned int h_active;
	unsigned int h_blanking;
	unsigned int h_sync_offset;
	unsigned int h_sync_width;

	unsigned int v_active;
	unsigned int v_blanking;
	unsigned int v_sync_offset;
	unsigned int v_sync_width;
};

static void framebuffer_mmcm_write(int adr, int data) {
	framebuffer_driver_clocking_mmcm_adr_write(adr);
	framebuffer_driver_clocking_mmcm_dat_w_write(data);
	framebuffer_driver_clocking_mmcm_write_write(1);
	while(!framebuffer_driver_clocking_mmcm_drdy_read());
}

/* FIXME: add vco frequency check */
static void framebuffer_get_clock_md(unsigned int pixel_clock, unsigned int *best_m, unsigned int *best_d)
{
	unsigned int ideal_m, ideal_d;
	unsigned int bm, bd;
	unsigned int m, d;
	unsigned int diff_current;
	unsigned int diff_tested;

	ideal_m = pixel_clock;
	ideal_d = 10000;

	bm = 1;
	bd = 0;
	for(d=1;d<=128;d++)
		for(m=2;m<=128;m++) {
			/* common denominator is d*bd*ideal_d */
			diff_current = abs(d*ideal_d*bm - d*bd*ideal_m);
			diff_tested = abs(bd*ideal_d*m - d*bd*ideal_m);
			if(diff_tested < diff_current) {
				bm = m;
				bd = d;
			}
		}
	*best_m = bm;
	*best_d = bd;
}

static void framebuffer_clkgen_write(int m, int d)
{
	/* clkfbout_mult = m */
	if(m%2)
		framebuffer_mmcm_write(0x14, 0x1000 | ((m/2)<<6) | (m/2 + 1));
	else
		framebuffer_mmcm_write(0x14, 0x1000 | ((m/2)<<6) | m/2);
	/* divclk_divide = d */
	if (d == 1)
		framebuffer_mmcm_write(0x16, 0x1000);
	else if(d%2)
		framebuffer_mmcm_write(0x16, ((d/2)<<6) | (d/2 + 1));
	else
		framebuffer_mmcm_write(0x16, ((d/2)<<6) | d/2);
	/* clkout0_divide = 10 */
	framebuffer_mmcm_write(0x8, 0x1000 | (5<<6) | 5);
	/* clkout1_divide = 2 */
	framebuffer_mmcm_write(0xa, 0x1000 | (1<<6) | 1);
}

void framebuffer_init(void)
{
	unsigned int m, d;
	struct video_timing mode = {
		// 640x480 @ 75Hz
		.pixel_clock = 3150,

		.h_active = 640,
		.h_blanking = 200,
		.h_sync_offset = 16,
		.h_sync_width = 64,

		.v_active = 480,
		.v_blanking = 20,
		.v_sync_offset = 1,
		.v_sync_width = 3,
	};

	printf("Initializing framebuffer console to %dx%d @ %dHz\n",
		mode.h_active,
		mode.v_active,
		(mode.pixel_clock*10000)/((mode.h_active + mode.h_blanking)*(mode.v_active + mode.v_blanking)));

	/* configure clock */
	framebuffer_get_clock_md(10*(mode.pixel_clock), &m, &d);
	framebuffer_clkgen_write(m, d);

	/* configure timings */
	framebuffer_core_initiator_hres_write(mode.h_active);
	framebuffer_core_initiator_vres_write(mode.v_active);

	framebuffer_core_initiator_hsync_start_write(mode.h_active + mode.h_sync_offset);
	framebuffer_core_initiator_hsync_end_write(mode.h_active + mode.h_sync_offset + mode.h_sync_width);
	framebuffer_core_initiator_hscan_write(mode.h_active + mode.h_blanking);

	framebuffer_core_initiator_vsync_start_write(mode.v_active + mode.v_sync_offset);
	framebuffer_core_initiator_vsync_end_write(mode.v_active + mode.v_sync_offset + mode.v_sync_width);
	framebuffer_core_initiator_vscan_write(mode.v_active + mode.v_blanking);

	/* configure dma */
	framebuffer_core_initiator_enable_write(0);
	framebuffer_core_initiator_base_write(0x10000000); // FIXME
	framebuffer_core_initiator_length_write(mode.h_active*mode.v_active*4);
	framebuffer_core_initiator_enable_write(1);
}
#endif