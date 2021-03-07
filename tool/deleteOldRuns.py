#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import json
import requests
from argparse import ArgumentParser


class GitActionCleaner():
    def __init__(self):
        # 某个 workflow run 记录保留多少个
        self.savedNumDefault = 10
        # GitHub API 请求头 Accept
        self.headerAccept = 'application/vnd.github.v3+json'
        self.httpSession = requests.session()
        # 初始化参数
        self.initEnv()

    def main(self):
        # 获取所有运行记录
        self.getAllRuns()
        # 删除已取消
        self.delRun(self.getCancelledIds())
        # 删除早期的
        self.delRun(self.getOldIds())

    def getCancelledIds(self):
        """删除所有取消状态的 workflow run 记录"""
        cancelledIds = []
        l = len(self.runs) - 1
        for i in range(l, -1, -1):
            run = self.runs[i]
            if run['conclusion'] == 'cancelled':
                # 提取id
                cancelledIds.append(run['id'])
                # 从列表中删除
                self.runs.remove(run)
        print('删除已经取消的记录:', cancelledIds)
        return cancelledIds

    def getOldIds(self):
        """删除指定name的workflow早期的 run 记录"""
        oldIds = []
        for run in self.runs:
            if run['name'] == self.wfName:
                oldIds.append(run['id'])
        print('删除比较老的记录:', oldIds)
        return oldIds[self.savedNum:]

    def delRun(self, runIds):
        """通过id删除运行记录"""
        for runId in runIds:
            res = self.httpSession.delete(f'{self.gitApi}/{runId}')
            print(res.text)

    def getAllRuns(self):
        """获取当前仓库action的所有运行记录 分页最大一次获取100条"""
        runs = self.httpSession.get(f"{self.gitApi}?per_page=100")
        self.runs = runs.json()['workflow_runs']

    def initEnv(self):
        """初始化所需数据"""
        # 提取输入参数
        self.args = self.getArgs()
        # GitHub token
        self.gitToken = self.args.gitToken
        # 当前flow的名字
        self.wfName = self.args.wfName
        # 保留的记录数量
        self.savedNum = self.args.savedNum
        # API 地址
        self.gitApi = f'https://api.github.com/repos/{self.args.gitRepo}/actions/runs'
        # 请求头
        header = {'Accept': self.headerAccept, 'Authorization': f'token {self.gitToken}'}
        self.httpSession.headers.update(header)

    def getArgs(self):
        """解析脚本调用入参
        ---------------------------------------------
            返回 argparse.ArgumentParser.parse_args() 格式的所有参数信息 """
        parser = ArgumentParser(description='用于删除指定名字的workflow过早的运行记录')
        parser.add_argument('-wn', dest='wfName', metavar='workflow name', type=str, default=os.environ['GITHUB_WORKFLOW'], help='将要处理的workflow名字, 必需, 若不从调用中传入则从环境变量 GITHUB_WORKFLOW 中提取')
        parser.add_argument('-gt', dest='gitToken', metavar='github token', type=str, default=os.environ['GIT_API_TOKEN'], help='GitHub API Token, 必需, 若不从调用中传入则从环境变量 GIT_API_TOKEN 中提取')
        parser.add_argument('-gp', dest='gitRepo', metavar='github repository path', type=str, default=os.environ['GITHUB_REPOSITORY'], help='要删除action的用户名/仓库名 如inused/actionTest, 若不传入则从环境变量 GITHUB_REPOSITORY 提取')
        parser.add_argument('-sn', dest='savedNum', metavar='saved workflow number', type=int, default=self.savedNumDefault, help=f'某个 workflow run 记录保留多少个,默认 {self.savedNumDefault}')
        return parser.parse_args()

if __name__ == '__main__':
    GitActionCleaner().main()