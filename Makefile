# Kernel source tree to use
KSRC := ../kernel

# Full .config files provided, and the defconfig files generated from them
CONFIG_SRC := 4.4/arm/siemens_dcu2.config 4.4/x86/plathome_obsvx1.config 4.4/x86/siemens_i386-rt.config 4.4/x86/siemens_iot2000.config \
	4.19/arm/siemens_imx6.config 4.19/x86/plathome_obsvx2.config 4.19/x86/siemens_i386-rt.config 4.19/x86/siemens_iot2000.config 4.19/x86/toshiba_atom_baytrail_cip.config
DEFCONFIG_GEN := $(CONFIG_SRC:%.config=%_defconfig)

# defconfig files provided, and the full .config files generated from them
DEFCONFIG_SRC := $(filter-out $(DEFCONFIG_GEN),$(wildcard */*/*_defconfig))
CONFIG_GEN := $(DEFCONFIG_SRC:%_defconfig=%.config)

# Lists of used sources
SOURCES_GEN := $(patsubst %.config,%.sources,$(CONFIG_SRC) $(CONFIG_GEN))

VERSIONS := $(wildcard [4-9].*)
CONFIG_ALL := $(patsubst %,%/all-enabled,$(VERSIONS))

# All generated files *except* sources lists, which take a very long time to
# regenerate
ALL_GEN := $(sort $(DEFCONFIG_GEN) $(CONFIG_GEN) $(CONFIG_ALL))

all : $(ALL_GEN)
all_sources : $(sort $(SOURCES_GEN))
clean :
	rm -f $(ALL_GEN)
clean_sources :
	rm -f $(sort $(SOURCES_GEN))
.PHONY : all all_sources clean clean_sources

CROSS_COMPILE = $(shell scripts/cross-compile-prefix $(ARCH) $<)

# Convert full .config to defconfig
%_defconfig : VERSION = $(word 1,$(subst /, ,$@))
%_defconfig : ARCH = $(word 2,$(subst /, ,$@))
$(DEFCONFIG_GEN) : %_defconfig : %.config
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	cp $< $(KSRC)/.config
	cd $(KSRC) && $(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) savedefconfig
	mv $(KSRC)/defconfig $@

# Convert defconfig to full .config
%.config : VERSION = $(word 1,$(subst /, ,$@))
%.config : ARCH = $(word 2,$(subst /, ,$@))
$(CONFIG_GEN) : %.config : %_defconfig
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	cp $< $(KSRC)/arch/$(ARCH)/configs/temp_defconfig
	cd $(KSRC) && $(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) temp_defconfig
	cd $(KSRC) && rm -f $(KSRC)/arch/$(ARCH)/configs/temp_defconfig
	mv $(KSRC)/.config $@

# Get used sources for .config
%.sources : VERSION = $(word 1,$(subst /, ,$@))
%.sources : ARCH = $(word 2,$(subst /, ,$@))
$(SOURCES_GEN) : %.sources : %.config
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	+scripts/get_used_sources.py $(KSRC) $< $(MFLAGS) \
		ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) > $@ \
		|| { rm -f $@ ; exit 1; }

%/all-enabled : export LC_ALL := C
%/all-enabled : VERSION = $*
# Can't use $* to select dependencies, as automatic variables are not
# defined until the recipe runs
$(foreach version,$(VERSIONS),\
$(eval $(version)/all-enabled : $(filter $(version)/%,$(CONFIG_SRC) $(CONFIG_GEN)))\
)
%/all-enabled :
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	scripts/kconfig_annotate.py $(KSRC) $^ > $@

.NOTPARALLEL:
