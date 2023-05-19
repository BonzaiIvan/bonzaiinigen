import re
import math
import os


# def read parafile
# def getpara_file()

# autobox for SC520HS
class AutoBox:
    para = {}
    reg = {}

    def __init__(self):
        self.para['y_pix_top_border'] = 16
        self.para['y_pix_btm_border'] = 32
        self.para['y_pix_array'] = 6048
        self.para['x_pix_top_border'] = 16
        self.para['x_pix_btm_border'] = 32
        self.para['x_pix_array'] = 6048

    def loadpara(self, parafile):
        with open(parafile) as fid:
            lines = fid.readlines()
        for line in lines:
            line = line.strip()
            if line=="":
                continue
            cells = line.split()
            para_key = cells[0].strip()
            para_val = cells[1].strip()
            self.update_para_key(para_key, para_val)
            # if para_key in self.para:
            # self.update_para_key(para_key,para_val)

    def update_para_key(self, para_key, para_val):
        if re.match(r"0x", para_val):
            val = int(para_val, 16)
        elif re.match(r"\d", para_val):
            val = int(para_val)
        else:
            val = para_val
        self.para[para_key] = val

    def genini(self,reg_file,ini_file):
        CHN = self.para['CHN']
        y_pix_size = self.para['y_pix_top_border'] + self.para['y_pix_btm_border'] + self.para['y_pix_array']
        x_pix_size = self.para['x_pix_top_border'] + self.para['x_pix_btm_border'] + self.para['x_pix_array']
        x_output_size = self.para['x_output_size']
        y_output_size = self.para['y_output_size']

        y_ideal_output_start_adr = (self.para['y_pix_top_border'] + (self.para['y_pix_array'] - self.para['y_output_size'] * self.para['Ana_Vbin']) / 2)
        y_ideal_output_end_adr = y_ideal_output_start_adr + self.para['y_output_size'] * self.para['Ana_Vbin'] - 1
        y_ideal_samp_start_adr = y_ideal_output_start_adr - self.para['y_img_win_cut'] * self.para['Ana_Vbin']
        if y_ideal_samp_start_adr < 0:
            print("Warning, y_ideal_samp_start_adr < 0")
        y_samp_top_border = self.para['y_img_win_cut'] * self.para['Ana_Vbin']
        y_samp_btm_border = y_samp_top_border
        y_samp_start = y_ideal_samp_start_adr + self.para['y_optical_offset']
        y_samp_end = y_ideal_output_end_adr + y_samp_btm_border + self.para['y_optical_offset']
        y_pipeline_blc_size = (self.para['blc_end_adr'] - self.para['blc_start_adr'] + 1) / self.para['Ana_Vbin']
        y_samp_size = y_samp_end - y_samp_start + 1
        if self.para['y_blc_win_en'] == 1:
            y_pipeline_win_cut = self.para['y_img_win_cut'] + y_pipeline_blc_size
        else:
            y_pipeline_win_cut = self.para['y_img_win_cut']

        x_ideal_output_start_adr = (self.para['x_pix_top_border'] + (self.para['x_pix_array'] - self.para['x_output_size'] * self.para['Ana_Hbin']) / 2)
        x_ideal_output_end_adr = x_ideal_output_start_adr + self.para['x_output_size'] * self.para['Ana_Hbin'] - 1
        x_ideal_samp_start_adr = x_ideal_output_start_adr - self.para['x_img_win_cut'] * self.para['Ana_Hbin']
        if x_ideal_samp_start_adr < 0:
            print("Warning, x_ideal_samp_start_adr < 0")
        x_samp_top_border = self.para['x_img_win_cut'] * self.para['Ana_Hbin']
        x_samp_btm_border = x_samp_top_border
        x_samp_start = x_ideal_samp_start_adr + self.para['x_optical_offset']
        x_samp_end = x_ideal_output_end_adr + x_samp_btm_border + self.para['x_optical_offset']
        x_samp_size = x_samp_end - x_samp_start + 1
        x_pipeline_win_cut = self.para['x_img_win_cut']

        # OTP_DPC40 bayer坐标
        otpdpc40_y_start = y_samp_start / 2
        otpdpc40_y_end = (y_samp_end + 1) / 2 + y_pipeline_blc_size * 2 -1

        # BLC 调整
        black_rb_ofst = (self.para['blc_start_adr'] / self.para['Ana_Vbin']) % 8
        array_rb_ofst = (y_samp_start / self.para['Ana_Vbin']) % 8

        # Fullsize Mode PD Window
        if self.para['config_mode'] == "fullsize":
            dly1 = 5  # PipeLine到vfifo的延迟
            dly2 = 2  # vfifo同步延迟
            dly3 = 4  # PD读出位置延迟
            pd_read_buf_ln = y_pipeline_win_cut + dly1 + dly2 + dly3
            pd_write_buf_ln = ((pd_read_buf_ln // 4) - 1) * 4 + 3
            if pd_read_buf_ln == pd_write_buf_ln:
                print("Warning, fullsize Vfifo Buffer Conflict")
            pd_cut_num = (pd_read_buf_ln // 4) - 1
            pd_y_win_st = pd_cut_num * 4
            pd_y_ideal_outputsize = self.para['y_output_size'] / 4  # img 坐标系
            pd_y_top_cut = 0
            pd_y_btm_cut = 0
            # pd_y_size = pd_y_ideal_outputsize - pd_y_top_cut - pd_y_btm_cut
            pd_y_win_size = pd_y_ideal_outputsize * 4

            pd_x_win_st = self.para['x_img_win_cut'] / 2
            pd_x_win_size = self.para['x_output_size'] / 2
            pd_hsize_man = x_samp_size / 2  # 供pdcomb12使用

        elif self.para['config_mode'] == "RSRS":
            dly1 = 6  # PipeLine到vfifo的延迟
            dly2 = 0  # vfifo同步延迟
            dly3 = 0  # PD读出位置延迟
            pd_read_buf_ln = y_pipeline_win_cut + dly1 + dly2 + dly3
            # pd_write_buf_ln = ((pd_read_buf_ln//4)-1)*4+3
            pd_cut_num = (pd_read_buf_ln // 4) - 1
            pd_y_win_st = pd_cut_num * 4
            pd_y_ideal_outputsize = self.para['y_output_size'] / 4  # img 坐标系
            pd_y_top_cut = 0
            pd_y_btm_cut = 0
            # pd_y_size = pd_y_ideal_outputsize
            pd_y_win_size = pd_y_ideal_outputsize * 4  # img 坐标系

            pd_x_win_st = self.para['x_img_win_cut']
            pd_x_win_size = self.para['x_output_size']  # img 坐标系
            pd_hsize_man = x_samp_size  # 供pdcomb12使用
        else :
            # 3%, 6% summing,ndol,fdol,V2H2
            pd_y_win_st = y_pipeline_win_cut
            pd_y_win_size = self.para['y_output_size']
            pd_x_win_st = x_pipeline_win_cut
            pd_hsize_man = ((self.para['x_output_size']/self.para['pd_x_density'])//CHN) * CHN * 2
            pd_x_win_size = math.ceil(float(pd_hsize_man/128)) * 128

        pd_win_dumy_en = 1

        # PD抽点 用于3% 6%.
        basic_pd_ptrn = [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
        # 0 1 2 3
        # 4 5 6 7
        # 8 9 a b
        # c d e f
        basic_pd_ptrn_value = 0
        for i in range(0,16):
            j = 15- i
            basic_pd_ptrn_value = basic_pd_ptrn_value + basic_pd_ptrn[j]*(2**j)

        # basic_gtpd_y_ofst = 1  # 原始偏移, 基于pixel打点
        basic_gtpd_y_ofst = self.para['basic_gtpd_y_ofst']
        basic_gtpd_x_ofst = self.para['basic_gtpd_x_ofst']

        if self.para['y_blc_win_en']:
            global_pd_y_st = y_pipeline_blc_size + basic_gtpd_y_ofst
        else:
            global_pd_y_st = basic_gtpd_y_ofst
        global_pd_y_end = global_pd_y_st + y_pix_size/self.para['Ana_Vbin']
        global_pd_x_st = basic_gtpd_x_ofst
        global_pd_x_end = global_pd_x_st + x_pix_size / self.para['Ana_Hbin']

        # Y方向
        pdb_y_adr_st = y_samp_start / self.para['Ana_Vbin']
        if self.para['y_blc_win_en'] == 1:
            pdb_y_adr_end = (y_samp_end + y_pipeline_blc_size * self.para['Ana_Vbin'] * 2 + 1) / self.para['Ana_Vbin'] - 1
        else:
            pdb_y_adr_end = (y_samp_end + 1) / self.para['Ana_Vbin'] - 1
        pd_y_num_pre_comb = self.para['y_output_size'] / self.para['pd_y_density']
        pd_y_num = pd_y_num_pre_comb / 2
        pd_y_delta = ((y_samp_start + self.para['y_img_win_cut'] * self.para['Ana_Vbin']) / self.para['Ana_Vbin']) % 16
        pd_y_delta_type = pd_y_delta // 4
        if pd_y_delta_type == 0:
            pd_ptrn_y_shf = 0
            gtpd_y_shf = 0
        elif pd_y_delta_type == 1:
            pd_ptrn_y_shf = 0
            gtpd_y_shf = -1
        elif pd_y_delta_type == 2:
            pd_ptrn_y_shf = 2
            gtpd_y_shf = 0
        elif pd_y_delta_type == 3:
            pd_ptrn_y_shf = 2
            gtpd_y_shf = -1
        gtpd_y_shf = gtpd_y_shf + (pd_y_delta % 4)
        # PD抽点时上边界切除 gtpd_y_shf, 下边界切除 gtpd_y_shf保持对称
        if self.para['y_blc_win_en'] == 1:
            gtpd_y_st = (pdb_y_adr_st + self.para['y_img_win_cut'] + y_pipeline_blc_size + gtpd_y_shf * 4 + basic_gtpd_y_ofst)
        else:
            gtpd_y_st = (pdb_y_adr_st + self.para['y_img_win_cut'] + gtpd_y_shf * 4 + basic_gtpd_y_ofst)
        gtpd_y_end = (pd_y_num_pre_comb - (gtpd_y_shf * 2)) * self.para['pd_y_density'] + gtpd_y_st - 1

        # X方向
        # basic_gtpd_x_ofst = 2  # 原始偏移, 基于pixel打点
        pdb_x_adr_st = x_samp_start / self.para['Ana_Hbin']
        pdb_x_adr_end = (x_samp_end + 1) / self.para['Ana_Hbin'] - 1
        pd_x_num_pre_comb = self.para['x_output_size'] / self.para['pd_x_density']
        pd_x_num = pd_x_num_pre_comb * 2
        pd_x_delta = ((x_samp_start + self.para['x_img_win_cut'] * self.para['Ana_Hbin']) / self.para['Ana_Hbin']) % 16
        # Bayer Based
        pd_x_delta_type = pd_x_delta // 4
        if pd_x_delta_type == 0:
            pd_ptrn_x_shf = 0
            gtpd_x_shf = 0
        elif pd_x_delta_type == 1:
            pd_ptrn_x_shf = 1
            gtpd_x_shf = 0
        elif pd_x_delta_type == 2:
            pd_ptrn_x_shf = 2
            gtpd_x_shf = 0
        elif pd_x_delta_type == 3:
            pd_ptrn_x_shf = 3
            gtpd_x_shf = 0
        gtpd_x_st = (pdb_x_adr_st + self.para['x_img_win_cut'] + gtpd_x_shf * 4 + basic_gtpd_x_ofst)
        gtpd_x_end = (pd_x_num_pre_comb - (gtpd_x_shf * 2)) * self.para['pd_x_density'] + gtpd_x_st - 1
        pdb_pd_ptrn = []
        pdb_pd_ptrn_value = 0
        for y in range(0,4):
            for x in range(0,4):
                k = ((y + pd_ptrn_y_shf)%4)*4 + ((x + pd_ptrn_x_shf)%4)
                pdb_pd_ptrn.append(basic_pd_ptrn[k])
        for i in range(0,16):
            j = 15-i
            pdb_pd_ptrn_value = pdb_pd_ptrn_value + pdb_pd_ptrn[j]*(2**j)

        #Print RegVar.
        print("autogen_down")

        with open(reg_file) as rid:
            lines = rid.readlines()
        cfglines = []

        for line in lines:
            line = line.strip()
            if line=="":
                continue
            cells = line.split()
            regadr = cells[0].strip()
            myvar_name = cells[1].strip()
            myvar_value = -1
            msb = -1
            lsb = -1
            if len(cells)>2:
                msb = int(cells[2])
            if len(cells) > 3:
                lsb = int(cells[3])
            #exestr = "myvar_value = "+myvar_name
            #exec(exestr)
            myvar_value = eval(myvar_name)
            if msb>=0 and lsb>=0 and msb>=lsb :
                limit = (2**(msb+1))
                cut = myvar_value%limit
                truncat = cut//(2**lsb)
            else:
                truncat = myvar_value

            reg_dec = int(truncat)
            reg_hex = hex(reg_dec)
            cfg_line = regadr + "," + reg_hex + "," + "\n"
            cfglines.append(cfg_line)
        print("load reg done")
        with open(ini_file,'w') as wid:
            wid.writelines(cfglines)







